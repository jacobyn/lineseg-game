""" The Bandit Game! """

from wallace.experiments import Experiment
from wallace.nodes import Agent, Source
# from wallace.models import Info, Node, Network
from wallace.networks import DiscreteGenerational
from wallace.information import Gene
from psiturk.models import Participant
import random
from json import dumps
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast
from sqlalchemy import Integer
from flask import Blueprint, Response, request, render_template
import os
from psiturk.psiturk_config import PsiturkConfig
import requests
from wallace import db
config = PsiturkConfig()


class BanditGame(Experiment):

    def __init__(self, session):
        super(BanditGame, self).__init__(session)

        # Wallace parameters
        self.task = "The Bandit Game"
        self.verbose = True
        self.experiment_repeats = 21
        self.practice_repeats = 3
        self.agent = BanditAgent
        self.min_acceptable_performance = 0
        self.generation_size = 20
        self.network = lambda: BanditGenerational(generations=40,
                                                  generation_size=self.generation_size,
                                                  initial_source=False)
        self.bonus_payment = 0
        self.initial_recruitment_size = self.generation_size
        self.instruction_pages = ["instructions/instruct-1.html",
                                  "instructions/instruct-2.html",
                                  "instructions/instruct-3.html"]
        self.debrief_pages = ["debriefing/debrief-1.html"]

        # BanditGame parameters
        self.n_trials = 10
        self.n_bandits = 5
        self.n_options = 10
        self.n_pulls = 10
        self.f_min = 2
        self.memory_cost = 2

        if not self.networks():
            self.setup()
        self.save()

    def setup(self):
        super(BanditGame, self).setup()
        for net in self.networks():
            source = GeneticSource(network=net)
            source.create_genes()
            for bandit in range(self.n_bandits):
                b = Bandit(network=net)
                b.bandit_id = bandit
                b.num_tiles = self.n_options
                b.treasure_tile = int(random.random()*self.n_options)

    def recruit(self):
        self.log("running recruit")
        participants = Participant.query.with_entities(Participant.status).all()

        # if all network are full close recruitment
        if not self.networks(full=False):
            self.log("all networks full, closing recruitment")
            self.recruiter().close_recruitment()
        # if a complete generation has finished and no-one is playing, recruit
        elif (len([p for p in participants if p.status == 101]) % self.generation_size == 0 and
              not [p for p in participants if p.status < 100]):
            self.log("generation finished, recruiting another")
            self.recruiter().recruit_participants(n=self.generation_size)
        else:
            self.log("generation not finished, not recruiting")

    # def submission_successful(self, participant):
    #     # is this participant the final one in the generation?
    #     participants = Participant.query.with_entities(Participant.status).all()
    #     if len([p for p in participants if p.status == 101]) % self.generation_size == 0:
    #         self.log("Participant was final in generation, working out everyone's payoff")

    #         # if yes, work out what generation has just finished
    #         generation = (CooperationAgent.query.
    #                       filter_by(participant_id=participant.uniqueid).
    #                       all())[0].generation
    #         self.log("Generation to finish was {}".format(generation))
    #         nodes = CooperationAgent.query.filter_by(generation=generation, failed=False).all()
    #         nets = Network.query.all()

    #         # first work out the payoffs for every decision
    #         for net in nets:
    #             levels = net.levels
    #             nets_nodes = [n for n in nodes if n.network_id == net.id]
    #             net_groups = set([n.group for n in nets_nodes])
    #             for group in net_groups:
    #                 group_nodes = [n for n in nets_nodes if n.group == group]
    #                 decisions = Decision.query.filter(Decision.origin_id.in_([n.id for n in group_nodes])).all()

    #                 level_1_decisions = [d for d in decisions if d.level == 1]
    #                 num_cooperate_1 = sum([int(d.contents) for d in level_1_decisions])
    #                 num_defect_1 = self.generation_size - num_cooperate_1
    #                 if levels > 1:
    #                     level_2_decisions = [d for d in decisions if d.level == 2]
    #                     num_cooperate_2 = sum([int(d.contents) for d in level_2_decisions])
    #                     num_defect_2 = self.generation_size - num_cooperate_2
    #                 if levels > 2:
    #                     level_3_decisions = [d for d in decisions if d.level == 3]
    #                     num_cooperate_3 = sum([int(d.contents) for d in level_3_decisions])

    #                 pot = num_cooperate_1*self.cost_of_cooperation*self.pot_multiplier
    #                 share = pot/float(self.generation_size)

    #                 for node in group_nodes:
    #                     level_1_decision = [d for d in level_1_decisions if d.origin_id == node.id][0]
    #                     l1d = int(level_1_decision.contents)
    #                     if levels > 1:
    #                         level_2_decision = [d for d in level_2_decisions if d.origin_id == node.id][0]
    #                         l2d = int(level_2_decision.contents)
    #                     if levels > 2:
    #                         level_3_decision = [d for d in level_3_decisions if d.origin_id == node.id][0]
    #                         l3d = int(level_3_decision.contents)
    #                     if levels == 1:
    #                         level_1_decision.payoff = share - l1d*self.cost_of_cooperation
    #                     else:
    #                         level_1_decision.payoff = (share - l1d*self.cost_of_cooperation -
    #                                                    (1-l1d)*(num_cooperate_2 - l2d)*self.value_of_punishment)
    #                         if levels == 2:
    #                             level_2_decision.payoff = 0 - l2d*(num_defect_1 - (1-l1d))*self.cost_of_punishment
    #                         else:
    #                             level_2_decision.payoff = (0 - l2d*(num_defect_1 - (1-l1d))*self.cost_of_punishment -
    #                                                        (1-l2d)*(num_cooperate_3 - l3d)*self.value_of_punishment)
    #                             level_3_decision.payoff = 0 - l3d*(num_defect_2 - (1-l2d))*self.cost_of_punishment

    #                     # use this to assign a score to every node
    #                     if levels == 1:
    #                         node.score = level_1_decision.payoff
    #                     elif levels == 2:
    #                         node.score = level_1_decision.payoff + level_2_decision.payoff
    #                     elif levels == 3:
    #                         node.score = level_1_decision.payoff + level_2_decision.payoff + level_3_decision.payoff

    #             # at this point, prompt the Summary source in each network to make a new Summary
    #             source = net.nodes(type=SummarySource)[0]
    #             source.summarize(generation=generation)

    #         # now get all the participants and pay them a bonus
    #         p_ids = set([n.participant_id for n in nodes])
    #         participants = Participant.query.filter(Participant.uniqueid.in_(p_ids)).all()
    #         for p in participants:
    #             p_nodes = [n for n in nodes if n.participant_id == p.uniqueid]
    #             score = sum([n.score for n in p_nodes])
    #             bonus = score/100
    #             if bonus < 0:
    #                 bonus = 0
    #             elif bonus > self.bonus_payment:
    #                 bonus = self.bonus_payment
    #             p.bonus = bonus
    #             if self.contactAWS:
    #                 self.recruiter().reward_bonus(
    #                     participant.assignmentid,
    #                     bonus,
    #                     self.bonus_reason())

    def data_check(self, participant):
        ### This needs to be written! ###

        self.log("Data check passed")
        return True


class BanditGenerational(DiscreteGenerational):

    __mapper_args__ = {"polymorphic_identity": "bandit_generational"}

    def add_node(self, node):
        agents = self.nodes(type=Agent)
        num_agents = len(agents)
        current_generation = int((num_agents-1)/float(self.generation_size))
        node.generation = current_generation

        # current_generation_size = len([a for a in agents if a.generation == current_generation])
        # current_group = int((current_generation_size-1)/float(self.group_size))
        # node.group = current_group

        if current_generation == 0:
            source = GeneticSource.query.filter_by(network_id=self.id).one()
            source.connect(whom=node)
            source.transmit(to_whom=node, what=Gene)
        else:
            prev_agents = type(node).query\
                .filter_by(failed=False,
                           network_id=self.id,
                           generation=current_generation-1)\
                .all()
            prev_fits = [p.fitness for p in prev_agents]
            prev_probs = [(f/(1.0*sum(prev_fits))) for f in prev_fits]

            rnd = random.random()
            temp = 0.0
            for i, probability in enumerate(prev_probs):
                temp += probability
                if temp > rnd:
                    parent = prev_agents[i]
                    break

            parent.connect(whom=node)
            parent.transmit(what=Gene, to_whom=node)

        node.receive()

        bandits = Bandit.query.filter_by(network_id=self.id).all()
        node.connect(whom=bandits, direction="from")


class GeneticSource(Source):
    """ A source that initializes the genes of the first generation """

    __mapper_args__ = {"polymorphic_identity": "genetic_source"}

    def create_genes(self):
        MemoryGene(origin=self, contents=0)
        CuriosityGene(origin=self, contents=1)


class Bandit(Source):
    """ a bandit that you can play with """

    __mapper_args__ = {"polymorphic_identity": "bandit"}

    @hybrid_property
    def num_tiles(self):
        return int(self.property1)

    @num_tiles.setter
    def num_tiles(self, num_tiles):
        self.property1 = repr(num_tiles)

    @num_tiles.expression
    def num_tiles(self):
        return cast(self.property1, Integer)

    @hybrid_property
    def treasure_tile(self):
        return int(self.property2)

    @treasure_tile.setter
    def treasure_tile(self, treasure_tile):
        self.property2 = repr(treasure_tile)

    @treasure_tile.expression
    def treasure_tile(self):
        return cast(self.property2, Integer)

    @hybrid_property
    def bandit_id(self):
        return int(self.property3)

    @bandit_id.setter
    def bandit_id(self, bandit_id):
        self.property3 = repr(bandit_id)

    @bandit_id.expression
    def bandit_id(self):
        return cast(self.property3, Integer)



# class SummarySource(Source):
#     """" A source that makes summaries of a generation """

#     __mapper_args__ = {"polymorphic_identity": "summary_source"}

#     def send_summary(self, to_whom):

#         summary = Summary.query.filter_by(origin_id=self.id, generation=to_whom.generation-1, group=to_whom.group).one()
#         self.transmit(what=summary, to_whom=to_whom)

#     def summarize(self, generation):
#         agents = CooperationAgent.query.filter_by(network_id=self.network_id, generation=generation, failed=False).all()
#         groups = set([a.group for a in agents])
#         net = self.network
#         levels = net.levels

#         for g in groups:
#             group_agents = [a for a in agents if a.group == g]
#             group_size = len(group_agents)
#             agent_ids = [a.id for a in agents]
#             decisions = Decision.query.filter(Decision.origin_id.in_(agent_ids)).all()

#             level_1_decisions = [d for d in decisions if d.level == 1]
#             num_cooperate_1 = sum([int(d.contents) for d in level_1_decisions])
#             num_defect_1 = group_size - num_cooperate_1
#             if levels > 1:
#                 level_2_decisions = [d for d in decisions if d.level == 2]
#                 num_cooperate_2 = sum([int(d.contents) for d in level_2_decisions])
#                 num_defect_2 = group_size - num_cooperate_2
#             else:
#                 num_cooperate_2 = 0
#                 num_defect_2 = 0
#             if levels > 2:
#                 level_3_decisions = [d for d in decisions if d.level == 3]
#                 num_cooperate_3 = sum([int(d.contents) for d in level_3_decisions])
#                 num_defect_3 = group_size - num_cooperate_3
#             else:
#                 num_cooperate_3 = 0
#                 num_defect_3 = 0

#             try:
#                 payoff_cooperate_1 = sum([d.payoff for d in level_1_decisions if int(d.contents) == 1])/float(num_cooperate_1)
#             except:
#                 payoff_cooperate_1 = None
#             try:
#                 payoff_defect_1 = sum([d.payoff for d in level_1_decisions if int(d.contents) == 0])/float(num_defect_1)
#             except:
#                 payoff_defect_1 = None
#             try:
#                 payoff_cooperate_2 = sum([d.payoff for d in level_2_decisions if int(d.contents) == 1])/float(num_cooperate_2)
#             except:
#                 payoff_cooperate_2 = None
#             try:
#                 payoff_defect_2 = sum([d.payoff for d in level_2_decisions if int(d.contents) == 0])/float(num_defect_2)
#             except:
#                 payoff_defect_2 = None
#             try:
#                 payoff_cooperate_3 = sum([d.payoff for d in level_3_decisions if int(d.contents) == 1])/float(num_cooperate_3)
#             except:
#                 payoff_cooperate_3 = None
#             try:
#                 payoff_defect_3 = sum([d.payoff for d in level_3_decisions if int(d.contents) == 0])/float(num_defect_3)
#             except:
#                 payoff_defect_3 = None

#             contents = {
#                 "num_cooperate_1": num_cooperate_1,
#                 "num_defect_1": num_defect_1,
#                 "num_cooperate_2": num_cooperate_2,
#                 "num_defect_2": num_defect_2,
#                 "num_cooperate_3": num_cooperate_3,
#                 "num_defect_3": num_defect_3,
#                 "payoff_cooperate_1": payoff_cooperate_1,
#                 "payoff_defect_1": payoff_defect_1,
#                 "payoff_cooperate_2": payoff_cooperate_2,
#                 "payoff_defect_2": payoff_defect_2,
#                 "payoff_cooperate_3": payoff_cooperate_3,
#                 "payoff_defect_3": payoff_defect_3,
#             }

#             summary = Summary(origin=self, contents=dumps(contents))
#             summary.generation = generation
#             summary.group = g


class MemoryGene(Gene):
    """ A gene that controls the time span of your memory """

    __mapper_args__ = {"polymorphic_identity": "memory_gene"}

    def _mutated_contents(self):
        if random.random() < 0.5:
            return max([self.contents + random.sample([-1, 1], 1)[0], 0])
        else:
            return self.contents


class CuriosityGene(Gene):
    """ A gene that controls your curiosity """

    __mapper_args__ = {"polymorphic_identity": "curiosity_gene"}

    def _mutated_contents(self):
        if random.random() < 0.5:
            return min([max([self.contents + random.sample([-1, 1], 1)[0], 0]), 40])
        else:
            return self.contents


# class Summary(Info):
#     """ A summary summarizes a generation of Agents """

#     __mapper_args__ = {"polymorphic_identity": "summary"}

#     @hybrid_property
#     def generation(self):
#         return int(self.property1)

#     @generation.setter
#     def generation(self, generation):
#         self.property1 = repr(generation)

#     @generation.expression
#     def generation(self):
#         return cast(self.property1, Integer)

#     @hybrid_property
#     def group(self):
#         return int(self.property2)

#     @group.setter
#     def group(self, group):
#         self.property2 = repr(group)

#     @group.expression
#     def group(self):
#         return cast(self.property2, Integer)


# class Decision(Info):

#     __mapper_args__ = {"polymorphic_identity": "decision"}

#     @hybrid_property
#     def level(self):
#         return int(self.property1)

#     @level.setter
#     def level(self, level):
#         self.property1 = repr(level)

#     @level.expression
#     def level(self):
#         return cast(self.property1, Integer)

#     @hybrid_property
#     def payoff(self):
#         return float(self.property2)

#     @payoff.setter
#     def payoff(self, payoff):
#         self.property2 = repr(payoff)

#     @payoff.expression
#     def payoff(self):
#         return cast(self.property2, Float)

class BanditAgent(Agent):

    __mapper_args__ = {"polymorphic_identity": "bandit_agent"}

    def update(self, infos):
        for info in infos:
            if isinstance(info, Gene):
                self.mutate(info_in=info)



# class CooperationAgent(Agent):

#     __mapper_args__ = {"polymorphic_identity": "cooperation_agent"}

#     @hybrid_property
#     def generation(self):
#         return int(self.property2)

#     @generation.setter
#     def generation(self, generation):
#         self.property2 = repr(generation)

#     @generation.expression
#     def generation(self):
#         return cast(self.property2, Integer)

#     @hybrid_property
#     def score(self):
#         return float(self.property3)

#     @score.setter
#     def score(self, score):
#         self.property3 = repr(score)

#     @score.expression
#     def score(self):
#         return cast(self.property3, Float)

#     @hybrid_property
#     def group(self):
#         return int(self.property4)

#     @group.setter
#     def group(self, group):
#         self.property4 = repr(group)

#     @group.expression
#     def group(self):
#         return cast(self.property4, Integer)


extra_routes = Blueprint(
    'extra_routes', __name__,
    template_folder='templates',
    static_folder='static')


# @extra_routes.route("/node/<int:node_id>/calculate_fitness", methods=["GET"])
# def calculate_fitness(node_id):

#     exp = CooperationGame(db.session)
#     node = CooperationGame.query.get(node_id)
#     if node is None:
#         exp.log("Error: /node/{}/calculate_fitness, node {} does not exist".format(node_id))
#         page = exp.error_page(error_type="/node/calculate_fitness, node does not exist")
#         js = dumps({"status": "error", "html": page})
#         return Response(js, status=400, mimetype='application/json')

#     node.calculate_fitness()
#     exp.save()

#     data = {"status": "success"}
#     return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/num_trials", methods=["GET"])
def get_num_trials():
    exp = BanditGame(db.session)
    data = {"status": "success",
            "experiment_repeats": exp.experiment_repeats,
            "practice_repeats": exp.practice_repeats,
            "n_trials": exp.n_trials}
    return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/num_bandits", methods=["GET"])
def get_num_bandits():
    exp = BanditGame(db.session)
    data = {"status": "success", "num_bandits": exp.n_bandits}
    return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/treasure_tile/<int:network_id>/<int:bandit_id>", methods=["GET"])
def get_treasure_tile(network_id, bandit_id):
    bandit = Bandit.query.filter_by(network_id=network_id, bandit_id=bandit_id).one()
    data = {"status": "success", "treasure_tile": bandit.treasure_tile}
    return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/consent", methods=["GET"])
def get_consent():
    return return_page('consent.html', request)


@extra_routes.route("/instructions/<int:page>", methods=["GET"])
def get_instructions(page):
    exp = BanditGame(db.session)
    return return_page(exp.instruction_pages[page-1], request)


@extra_routes.route("/debrief/<int:page>", methods=["GET"])
def get_debrief(page):
    exp = BanditGame(db.session)
    return return_page(exp.debrief_pages[page-1], request)


@extra_routes.route("/stage", methods=["GET"])
def get_stage():
    return return_page('stage.html', request)


@extra_routes.route("/participant/<worker_id>/<hit_id>/<assignment_id>", methods=["POST"])
def create_participant(worker_id, hit_id, assignment_id):
    exp = BanditGame(db.session)

    parts = Participant.query.filter_by(workerid=worker_id).all()
    if parts:
        print "participant already exists!"
        return Response(status=200)

    p = Participant(workerid=worker_id, assignmentid=assignment_id, hitid=hit_id)
    exp.save(p)
    return Response(status=200)


@extra_routes.route("/ad_address/<mode>/<hit_id>", methods=["GET"])
def ad_address(mode, hit_id):

    if mode == "debug":
        address = '/complete'
    elif mode in ["sandbox", "live"]:
        CONFIG = PsiturkConfig()
        CONFIG.load_config()
        username = os.getenv('psiturk_access_key_id', CONFIG.get("psiTurk Access", "psiturk_access_key_id"))
        password = os.getenv('psiturk_secret_access_id', CONFIG.get("psiTurk Access", "psiturk_secret_access_id"))
        try:
            req = requests.get('https://api.psiturk.org/api/ad/lookup/' + hit_id,
                               auth=(username, password))
        except:
            raise ValueError('api_server_not_reachable')
        else:
            if req.status_code == 200:
                hit_address = req.json()['ad_id']
            else:
                raise ValueError("something here")
        if mode == "sandbox":
            address = 'https://sandbox.ad.psiturk.org/complete/' + str(hit_address)
        elif mode == "live":
            address = 'https://ad.psiturk.org/complete/' + str(hit_address)
    else:
        raise ValueError("Unknown mode: {}".format(mode))
    return Response(dumps({"address": address}), status=200)


# @extra_routes.route("/info/<int:node_id>/<int:level>", methods=["POST"])
# def info_post(node_id, level):
#     exp = BanditGame(db.session)

#     # get the parameters
#     info_type = Decision

#     contents = request_parameter(request=request, parameter="contents")
#     if type(contents) == Response:
#         return contents

#     exp.log("/info/level POST request. Params: node_id: {}, info_type: {}, \
#              contents: {}, level: {}"
#             .format(node_id, info_type, contents, level))

#     # check the node exists
#     node = Node.query.get(node_id)
#     if node is None:
#         exp.log("Error: /info/{} POST, node does not exist".format(node_id))
#         page = error_page(error_type="/info POST, node does not exist")
#         js = dumps({"status": "error", "html": page})
#         return Response(js, status=400, mimetype='application/json')

#     # execute the request
#     info = info_type(origin=node, contents=contents)
#     info.level = level
#     exp.save()

#     # return the data
#     data = info.__json__()
#     data = {"status": "success", "info": data}
#     exp.log("/info POST request successful.")
#     js = dumps(data, default=date_handler)
#     return Response(js, status=200, mimetype='application/json')


def return_page(page, request):
    exp = BanditGame(db.session)
    try:
        hit_id = request.args['hit_id']
        assignment_id = request.args['assignment_id']
        worker_id = request.args['worker_id']
        mode = request.args['mode']
        return render_template(
            page,
            hit_id=hit_id,
            assignment_id=assignment_id,
            worker_id=worker_id,
            mode=mode
        )
    except:
        return exp.error_page(error_type="{} AWS args missing".format(page))


def request_parameter(request, parameter, parameter_type=None, default=None):
    """ Get a parameter from a request

    The request object itself must be passed.
    parameter is the name of the parameter you are looking for
    parameter_type is the type the parameter should have
    default is the value the parameter takes if it has not been passed

    If the parameter is not found and no default is specified,
    or if the parameter is found but is of the wrong type
    then a Response object is returned"""

    exp = BanditGame(db.session)

    # get the parameter
    try:
        value = request.values[parameter]
    except KeyError:
        # if it isnt found use the default, or return an error Response
        if default is not None:
            return default
        else:
            msg = "{} {} request, {} not specified".format(request.url, request.method, parameter)
            exp.log("Error: {}".format(msg))
            data = {
                "status": "error",
                "html": error_page(error_type=msg)
            }
            return Response(
                dumps(data),
                status=400,
                mimetype='application/json')

    # check the parameter type
    if parameter_type is None:
        # if no parameter_type is required, return the parameter as is
        return value
    elif parameter_type == int:
        # if int is required, convert to an int
        try:
            value = int(value)
            return value
        except ValueError:
            msg = "{} {} request, non-numeric {}: {}".format(request.url, request.method, parameter, value)
            exp.log("Error: {}".format(msg))
            data = {
                "status": "error",
                "html": error_page(error_type=msg)
            }
            return Response(
                dumps(data),
                status=400,
                mimetype='application/json')
    elif parameter_type == "known_class":
        # if its a known class check against the known classes
        try:
            value = exp.known_classes[value]
            return value
        except KeyError:
            msg = "{} {} request, unknown_class: {} for parameter {}".format(request.url, request.method, value, parameter)
            exp.log("Error: {}".format(msg))
            data = {
                "status": "error",
                "html": error_page(error_type=msg)
            }
            return Response(
                dumps(data),
                status=400,
                mimetype='application/json')
    elif parameter_type == bool:
        # if its a boolean, convert to a boolean
        if value in ["True", "False"]:
            return value == "True"
        else:
            msg = "{} {} request, non-boolean {}: {}".format(request.url, request.method, parameter, value)
            exp.log("Error: {}".format(msg))
            data = {
                "status": "error",
                "html": error_page(error_type=msg)
            }
            return Response(
                dumps(data),
                status=400,
                mimetype='application/json')
    else:
        msg = "/{} {} request, unknown parameter type: {} for parameter {}".format(request.url, request.method, parameter_type, parameter)
        exp.log("Error: {}".format(msg))
        data = {
            "status": "error",
            "html": error_page(error_type=msg)
        }
        return Response(
            dumps(data),
            status=400,
            mimetype='application/json')


def error_page(participant=None, error_text=None, compensate=True,
               error_type="default"):
    """Render HTML for error page."""
    if error_text is None:

        error_text = """There has been an error and so you are unable to
        continue, sorry! If possible, please return the assignment so someone
        else can work on it."""

        if compensate:
            error_text += """Please use the information below to contact us
            about compensation"""

    if participant is not None:
        hit_id = participant.hitid,
        assignment_id = participant.assignmentid,
        worker_id = participant.workerid
    else:
        hit_id = 'unknown'
        assignment_id = 'unknown'
        worker_id = 'unknown'

    return render_template(
        'error_wallace.html',
        error_text=error_text,
        compensate=compensate,
        contact_address=config.get(
            'HIT Configuration', 'contact_email_on_error'),
        error_type=error_type,
        hit_id=hit_id,
        assignment_id=assignment_id,
        worker_id=worker_id
    )


def date_handler(obj):
    """Serialize dates."""
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj
