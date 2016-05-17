""" The Lineseg Game! """

from wallace.experiments import Experiment
from wallace.nodes import Agent, Source
from wallace.models import Info, Network, Vector, Node
from wallace.networks import Chain
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

N_network_size=6;
N_network_size_practice=4;
K_repeats_size=3;
K_repeats_size_practice=2;
M_length=5;



class LineGame(Experiment):

    def __init__(self, session):
        super(LineGame, self).__init__(session)

        """ Wallace parameters """
        self.task = "The Line Game"
        self.verbose = True
        self.experiment_repeats = N_network_size  # N number of chains
        self.practice_repeats = N_network_size_practice    # N number of chains for practice
        self.agent = Agent
        self.network = lambda: MultiChain(max_size=M_length)
        self.bonus_payment = 0.5
        self.initial_recruitment_size = 1 # initital recuriemnt size (number of participants initally recruited)
        self.instruction_pages = ["instructions/instruct-1.html",
                                  "instructions/instruct-2.html",
                                  "instructions/instruct-3.html",
                                  "instructions/instruct-4.html",
                                  "instructions/instruct-5.html"]
        self.debrief_pages = ["debriefing/debrief-1.html"]

        if not self.networks():
            self.setup()
        self.save()

    def get_network_for_participant (self, participant_id):
        # get the participants nodes
        node_participated = Node.query.filter_by(participant_id=participant_id).all()
        # get all the networks
        all_networks = Network.query.all()

        # get the networks that the participant has participated in
        network_participated_ids = [n.network_id for n in node_participated]
        network_participated = [n for n in all_networks if n.id in network_participated_ids]

        # get the networks that are currently open
        open_networks = [n for n in all_networks if n.open == True]

        # get the open and unparticipated networks
        possible_networks = [net for net in open_networks if net.id not in network_participated_ids]

        # how many practice networks have they participated in
        num_practice_participated = len([n for n in network_participated if n.role == "practice"])

        # if they can keep practicing
        if (num_practice_participated < K_repeats_size_practice):
            possible_networks = [net for net in possible_networks if net.role == "practice"]
        else:
            # how many test networks have they participated in
            num_test_participated = len([n for n in network_participated if n.role != "practice"])
            # if they can keep going
            if (num_test_participated < K_repeats_size):
                possible_networks = [net for net in possible_networks if net.role != "practice"]
            else:
                return None

        if possible_networks:
            chosen_network = random.choice(possible_networks)
        else:
            return None

        # if (K_repeats_size>len(possible_test_networks)):
        #     return None

        chosen_network.open = False
        return chosen_network

    def node_post_request(self, participant_id, node):
        node.neighbors(connection="from")[0].transmit()
        node.receive()

    def info_post_request(self, node, info):
        try:
            res = int(info.contents)
        except:
            node.fail()

        node.network.open = True


    def setup(self):
        super(LineGame, self).setup()
        for net in self.networks():
            source = LineSource(network=net)
            source.create_pattern()
            net.open = True

    def recruit(self):
        pass
#        "" we will need to deal with it later""
        # self.log("running recruit")
        # participants = Participant.query.with_entities(Participant.status).all()

        # if all network are full close recruitment
        # if not self.networks(full=False):
        #     self.log("all networks full, closing recruitment")
        #     self.recruiter().close_recruitment()
        # # if a complete generation has finished and no-one is playing, recruit
        # elif (len([p for p in participants if p.status == 101]) % self.generation_size == 0 and
        #       not [p for p in participants if p.status < 100]):
        #     self.log("generation finished, recruiting another")
        #     self.recruiter().recruit_participants(n=self.generation_size)
        # else:
        #     self.log("generation not finished, not recruiting")

    def data_check(self, participant):
        return True
        #""" TBD """

    def bonus(self, participant):
        return 0.00

    # def attention_check(self, participant):
    #     bandits = Bandit.query.all()
    #     nodes = BanditAgent.query.filter_by(participant_id=participant.uniqueid).all()
    #     pulls = []
    #     for node in nodes:
    #         pulls.extend(node.infos(type=Pull))

    #     final_decisions = [p for p in pulls if p.check == "false"]
    #     checks = [p for p in pulls if p.check == "true"]

    #     times_found_treasure = 0
    #     times_chose_treasure = 0

    #     for d in final_decisions:
    #         if d.remembered == "false":
    #             right_answer = [b for b in bandits if b.network_id == d.network_id and b.bandit_id == d.bandit_id][0].good_arm
    #             checked_tiles = [int(c.contents) for c in checks if c.network_id == d.network_id and c.trial == d.trial]
    #             if right_answer in checked_tiles:
    #                 times_found_treasure += 1
    #                 if int(d.contents) == right_answer:
    #                     times_chose_treasure += 1

    #     diff = times_found_treasure - times_chose_treasure

    #     return diff < 300

    # NORIHERE:    The logic: #fail nodes / all nodes < Fail percent
    #                         $ property 1 (num of attempts) >1  / # trials < MoreHanOneAttemptPercent
########################### NORIHERE ################################
    def attention_check(self, participant):
        # how to retrieve failes nodes?
        # nodes = Agent.query.filter_by(participant_id=participant.uniqueid).all()
        # line_infos = []
        #  for node in nodes:
        #      line_infos.extend(node.infos)
        return True
########################### NORIHERE ################################

########################### NORIHERE ################################
# class LineInfo(Info):

#     __mapper_args__ = {"polymorphic_identity": "bandit_agent"}

#     @hybrid_property
#     def num_attempts(self):
#         return int(self.property1)

#     @num_attempts.setter
#     def num_attempts(self, my_num_attempts):
#         self.property1 = repr(my_num_attempts)

#     @num_attempts.expression
#     def num_attempts(self):
#         return cast(self.property1, Integer)


#     @hybrid_property
#     def reaction_time(self):
#         return float(self.property2)

#     @reaction_time.setter
#     def reaction_time(self, my_RT):
#         self.property2 = repr(my_RT)

#     @reaction_time.expression
#     def reaction_time(self):
#         return cast(self.property2, Integer)


#   @hybrid_property
#     def true_seed(self):
#         return int(self.property3)

#     @true_seed.setter
#     def true_seed(self, my_true_seed):
#         self.property3 = repr(my_true_seed)

#     @true_seed.expression
#     def true_seed(self):
#         return cast(self.property3, Integer)

#  @hybrid_property
#     def result_list(self):
#         return repr(self.property4)

#     @result_list.setter
#     def result_list(self, my_result_list):
#         self.property4 = repr(my_result_list)

#     @result_list.expression
#     def result_list(self):
#         return cast(self.property4, Integer)




    # def calculate_fitness(self):
    #     exp = BanditGame(db.session)

    #     my_decisions = Pull.query.filter_by(origin_id=self.id, check="false").all()
    #     bandits = Bandit.query.filter_by(network_id=self.network_id).all()

    #     pulls = exp.n_pulls
    #     curiosity = int(self.infos(type=CuriosityGene)[0].contents)
    #     memory = int(self.infos(type=MemoryGene)[0].contents)

    #     fitness = exp.f_min - memory*exp.memory_cost

    #     for d in my_decisions:
    #         bandit = [b for b in bandits if b.bandit_id == d.bandit_id][0]
    #         if int(d.contents) == bandit.good_arm:
    #             fitness += pulls
    #         if d.remembered == "false":
    #             fitness -= curiosity

    #     fitness = max([fitness, 0.0001])
    #     fitness = ((1.0*fitness)*exp.f_scale_factor)**exp.f_power_factor
    #     self.fitness = fitness

    # def _what(self):
    #     return Gene
########################### NORIHERE ################################


class MultiChain(Chain):

    __mapper_args__ = {"polymorphic_identity": "multi_chain"}

    @hybrid_property
    def open(self):
        return bool(self.property1)

    @open.setter
    def open(self, open):
        self.property1 = repr(open)

    @open.expression
    def open(self):
        return cast(self.property1, Boolean)


class LineSource(Source):
    """ A source that initializes the pattern of the first generation """

    __mapper_args__ = {"polymorphic_identity": "line_source"}

    def _what(self):
        return Info

    def create_pattern(self):
        Info(origin=self, contents=random.randint(0,100));


extra_routes = Blueprint(
    'extra_routes', __name__,
    template_folder='templates',
    static_folder='static')


# @extra_routes.route("/node/<int:node_id>/calculate_fitness", methods=["GET"])
# def calculate_fitness(node_id):

#     exp = BanditGame(db.session)
#     node = BanditAgent.query.get(node_id)
#     if node is None:
#         exp.log("Error: /node/{}/calculate_fitness, node {} does not exist".format(node_id))
#         page = exp.error_page(error_type="/node/calculate_fitness, node does not exist")
#         js = dumps({"status": "error", "html": page})
#         return Response(js, status=400, mimetype='application/json')

#     node.calculate_fitness()
#     exp.save()

#     data = {"status": "success"}
#     return Response(dumps(data), status=200, mimetype='application/json')


# @extra_routes.route("/num_trials", methods=["GET"])
# def get_num_trials():
#     exp = BanditGame(db.session)
#     data = {"status": "success",
#             "experiment_repeats": exp.experiment_repeats,
#             "practice_repeats": exp.practice_repeats,
#             "n_trials": exp.n_trials}
#     return Response(dumps(data), status=200, mimetype='application/json')


# @extra_routes.route("/num_bandits", methods=["GET"])
# def get_num_bandits():
#     exp = BanditGame(db.session)
#     data = {"status": "success", "num_bandits": exp.n_bandits}
#     return Response(dumps(data), status=200, mimetype='application/json')


# @extra_routes.route("/num_arms/<int:network_id>/<int:bandit_id>", methods=["GET"])
# def get_num_arms(network_id, bandit_id):
#     bandit = Bandit.query.filter_by(network_id=network_id, bandit_id=bandit_id).one()
#     data = {"status": "success", "num_arms": bandit.num_arms}
#     return Response(dumps(data), status=200, mimetype='application/json')


# @extra_routes.route("/good_arm/<int:network_id>/<int:bandit_id>", methods=["GET"])
# def good_arm(network_id, bandit_id):
#     bandit = Bandit.query.filter_by(network_id=network_id, bandit_id=bandit_id).one()
#     data = {"status": "success", "good_arm": bandit.good_arm}
#     return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/consent", methods=["GET"])
def get_consent():
    return return_page('consent.html', request)

@extra_routes.route("/is_practice/<int:network_id>", methods=["GET"])
def get_is_practice(network_id):
#    exp = LineGame(db.session)
    net=Network.query.get(network_id)
    data = {"status": "success", "is_practice": net.role == "practice"}
    return Response(dumps(data), status=200, mimetype='application/json')




@extra_routes.route("/instructions/<int:page>", methods=["GET"])
def get_instructions(page):
    exp = LineGame(db.session)
    return return_page(exp.instruction_pages[page-1], request)


@extra_routes.route("/debrief/<int:page>", methods=["GET"])
def get_debrief(page):
    exp = LineGame(db.session)
    return return_page(exp.debrief_pages[page-1], request)


@extra_routes.route("/stage", methods=["GET"])
def get_stage():
    return return_page('stage.html', request)


@extra_routes.route("/participant/<worker_id>/<hit_id>/<assignment_id>", methods=["POST"])
def create_participant(worker_id, hit_id, assignment_id):
    exp = LineGame(db.session)

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


def return_page(page, request):
    exp = LineGame(db.session)
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

    exp = LineGame(db.session)

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
