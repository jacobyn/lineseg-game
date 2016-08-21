""" The Vision Game with Thomas Langlois and Nori Jacoby"""
""" config for duration of the experiment"""

from wallace.experiments import Experiment
from wallace.nodes import Agent, Source
from wallace.models import Info, Network, Vector, Node, Participant
from wallace.networks import Chain
from wallace.information import Gene
import random
from json import dumps
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast
from sqlalchemy import Integer, Float
from flask import Blueprint, Response, request, render_template
import os
from psiturk.psiturk_config import PsiturkConfig
import requests
from wallace import db
config = PsiturkConfig()
from datetime import datetime
import math

def list_to_float_array(mystr):
    temp=mystr.replace('[','').replace(']','')
    return [float(x) for x in temp.split(',')]


class VisionGame(Experiment):

    def __init__(self, session):
        super(VisionGame, self).__init__(session)


        self.N_network_size=20
        self.N_network_size_practice=20
        self.K_repeats_size=10
        self.K_repeats_size_practice=5
        self.M_length=5
        self.bonus_payment = 0.5

        #experiment specific params
        range_min=[0., 0.]
        range_max=[1., 1.]
        my_dimensions=2



        ### ---> TAKECARE
        self.params= {"my_dimensions":my_dimensions,"range_min":range_min, "range_max":range_max}

        Percent_attention_trials=200.0 #number of failed trials should be a bout 2x than the number of trials hence 200%
        Percent_failed_nodes= 90 #number of trials that can fail from all reasons (for example 95% means subject wasn't listening 95% of the time and this would fail all his data)
        #self.Percent_failed_nodes= 25 #changed it to 25% becuase almost always subject are very good and make very few mistakes -- I TRIED THIS IS IS DANGEROUS BECAUSE OTHER NODES IMIDIATELY START FAIL...

        """ Wallace parameters """
        self.task = "The Visual Memory Game"
        self.verbose = False
        self.experiment_repeats = self.N_network_size  # N number of chains
        self.practice_repeats = self.N_network_size_practice    # N number of chains for practice
        self.K_all_trials=self.K_repeats_size+self.K_repeats_size_practice
        #self.agent = VisionAgent
        #self.network = lambda: MultiChain(max_size=self.M_length)

        self.initial_recruitment_size = 10 # initital recuriemnt size (number of participants initally recruited) ##IMPORTANT THIS SHOULD BE more than 10 becuase if not you only have 10 subjects.

        # this should be removed and taken care in the UI
        self.instruction_pages = ["instructions/instruct-1.html",
                                  "instructions/instruct-2.html",
                                  "instructions/instruct-3.html",
                                  "instructions/instruct-4.html",
                                  "instructions/instruct-5.html"]
        # this should be removed and taken care in the UI
        self.debrief_pages = ["debriefing/debrief-1.html"]
        self.known_classes["VisionInfo"] = VisionInfo
        self.known_classes["VisionSource"] = VisionSource


        if not self.networks():
            self.setup()
        self.save()

#depricated:
#    def node_type(self, network):
#        return VisionAgent
    def create_node(self, network, participant):
        return VisionAgent(network=network, participant=participant)

    def create_network(self):
       """Return a new network."""
       return MultiChain(max_size=self.M_length)

    def get_network_for_participant (self, participant):
        # get the participants nodes
        node_participated = Node.query.filter_by(participant_id=participant.id).all()
        # get all the networks
        all_networks = Network.query.all()

        # get the networks that the participant has participated in
        network_participated_ids = [n.network_id for n in node_participated]
        network_participated = [n for n in all_networks if n.id in network_participated_ids]

        # get the networks that are currently open
        open_networks = [n for n in all_networks if n.open and not n.full]

        # get the open and unparticipated networks
        possible_networks = [net for net in open_networks if net.id not in network_participated_ids]

        # how many practice networks have they participated in
        num_practice_participated = len([n for n in network_participated if n.role == "practice"])

        # if they can keep practicing
        if (num_practice_participated < self.K_repeats_size_practice):
            possible_networks = [net for net in possible_networks if net.role == "practice"]
        else:
            # how many test networks have they participated in
            num_test_participated = len([n for n in network_participated if n.role != "practice"])
            # if they can keep going
            if (num_test_participated < self.K_repeats_size):
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

    def node_post_request(self, participant, node):
        print "NODE POST REQUST HAD HAPPEND\n ########################\n#########################"
        #node.neighbors(connection="from")[0].transmit()
        print node.neighbors(direction="from")
        print node.neighbors(direction="from")[0]

        node.neighbors(direction="from")[0].transmit()
        node.receive()
        print node


    def add_node_to_network(self, node, network):
        """When a node is created it is added to the chain (see Chain in networks.py)
        and it receives any transmissions."""
        network.add_node(node)
        parent = node.neighbors(direction="from")[0]
        parent.transmit()
        node.receive()

    def info_post_request(self, node, info):
        try:
            res = str(info.contents)
            if res=='Nan':
                node.fail()
            else:
                result_as_float_arrray=list_to_float_array(res)
                assert(self.params["my_dimensions"]==len(result_as_float_arrray))

        except:
            node.fail()
        node.network.open = True


    def setup(self):
        super(VisionGame, self).setup()
        #print('-----------\ndebug\n----------\n')
        for net in self.networks():
           # print "network---->"
           # print net
            if net.role == "practice":
                net.max_size = 500
            source = VisionSource(network=net)
            seed=source.create_pattern(self.params)
            source.seed = seed
            source.generation = 0
            source.reaction_time = 0
            net.open = True

    def recruit(self):
        # participants = Participant.query.with_entities(Participant.status).all()

        # if all network are full close recruitment
        if not self.networks(full=False, role="experiment"):
             self.log("all networks full, closing recruitment")
             self.recruiter().close_recruitment()
        else:
            # ##### NORI ADD THIS DON"T
            # networks = Network.query.all()
            # remaining_nodes=0;
            # for net in networks:
            #     if net.role == "practice":
            #         continue
            #     remaining_nodes=remaining_nodes + Max(net.max_size-len(net.nodes(type=Agent)),0)
            # # to make the logic

            self.recruiter().recruit_participants(n=1)
        #     self.log("generation not finished, not recruiting")

    def data_check(self, participant):
              # get the necessary data
        networks = Network.query.all()
        nodes = VisionAgent.query.filter_by(participant_id=participant.id, failed=False).all()
        node_ids = [n.id for n in nodes]
        incoming_vectors = Vector.query.filter(Vector.destination_id.in_(node_ids)).all()
        outgoing_vectors = Vector.query.filter(Vector.origin_id.in_(node_ids)).all()

        try:
            # 1 source node per network
            for net in networks:
                sources = net.nodes(type=VisionSource)
                assert len(sources) == 1
                 # only one source for every network


            # 1 vector (incoming) per node
            for node in nodes:
                try:
                    assert len([v for v in outgoing_vectors if v.origin_id == node.id and not v.failed]) in [0,1]
                    assert len([v for v in incoming_vectors if v.destination_id == node.id]) == 1
                except:
                    print "Warning: problem with number of vectors (a)= " + str(len([v for v in outgoing_vectors if v.origin_id == node.id and not v.failed])) + " (b)= " + str(len([v for v in incoming_vectors if v.destination_id == node.id]))
                    node.fail()

                ## not failed nodes???? PERHAPS FILTER HERE OVER NOT FAILED NODES? IS IT AUDIO?
                infos =  node.infos(VisionInfo)
                #print ([type(i) for i in  infos])
                ################### NORI #################
                ###original:
                ### assert (len([i for i in infos ]) == 1)

                if (len([i for i in infos ]) != 1):
                    node.fail()
                else:
                    info=infos[0]

                    response=info.contents
                    dim=self.params.my_dimensions

                    if not response=='NaN':
                        response_as_float_array=list_to_float_array(response)
                        response_len=len(response_as_float_array)
                        if not response_len==dim:
                            print "error in data check len of response: {} was wrong: {} dimensions: {}".format(response,response_len,dim)
                        assert(response_len==dim)
                        for i in range(response_len):
                            v=response_as_float_array[i]
                            range_min=self.params.range_min[i]
                            range_max=self.params.range_max[i]
                            assert(v>=range_min)
                            assert(v<=range_max)

                    # ResponseRatio=info.contents
                    # TrueRatio=info.true_seed
                    # is_numeric = False
                    # try:
                    #     ResponseRatio=int(info.contents)
                    #     is_numeric = True
                    # except:
                    #     pass

                    # if is_numeric:
                    #     assert (abs(ResponseRatio-TrueRatio)<=self.UI_PROX_T)
                    # else:
                    #     assert (ResponseRatio=='NaN')

                    try:
                        assert len(node.transmissions(direction="all", status="pending")) == 0
                        assert len(node.transmissions(direction="incoming", status="received")) == 1
                    except:
                        print "Warning: had to fail nodes because of transmission error"
                        node.fail()

            self.log("Data check passed!")
            return True
        except:
            import traceback
            traceback.print_exc()
            return False


    def bonus(self, participant):
        tried_attempts=0
        good_trials=0
        overall_attempts=0;
        failed_nodes=0;
        not_good_trials=0;
        nodes = VisionAgent.query.filter_by(participant_id=participant.id).all()
        for node in nodes:
            if node.failed:
                failed_nodes+=1
                tried_attempts+=1
            else:
#                infos = node.infos(type=VisionInfo)
                infos = node.infos()
                for info in infos:
                    tried_attempts+=1
                    try:
                        num_attempts=int(info.property1)
                        #num_attempts=info.num_attempts
                    except:
                        num_attempts=0
                    if num_attempts==1:
                        good_trials+=1
                    if num_attempts>1:
                        not_good_trials+=1
        #self.log("\NORITHERE-len(nodes)= {} self.K_all_trials={} good_trials={}  failed_nodes={}".format(len(nodes),self.K_all_trials,good_trials,failed_nodes))
        score =  (0.2*len(nodes))/self.K_all_trials  + (0.8*good_trials)/self.K_all_trials #+ 0.2*(good_trials - failed_nodes ) * 1.0 / (tried_attempts)
        #score =  (1.0*good_trials)/self.K_all_trials
        score = score - 0.8*failed_nodes/self.K_all_trials - 0.5*not_good_trials/self.K_all_trials
        #score = round(score*100.0)/100.0
#        score = score*0.5 + 0.5
        #score = (good_trials - failed_nodes) * 1.0 / (tried_attempts)
        score = max (score, 0.02)
        score = min (score, 0.95)

        #if tried_attempts<5:
        #    score=0.10
        to_return_score=round(score*self.bonus_payment*100.0)/100.0
        return to_return_score

    # def attention_check(self, participant):
    #     bandits = Bandit.query.all()
    #     nodes = BanditAgent.query.filter_by(participant_id=participant.id).all()
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
        tried_attempts=0
        tried_trials=0
        failed_nodes=0;
        nodes = VisionAgent.query.filter_by(participant_id=participant.id).all()
        for node in nodes:
            if node.failed:
                failed_nodes+=1
            else:
                infos =  node.infos(type=VisionInfo)
                for info in infos:
                     tried_attempts+=info.num_attempts
                     tried_trials+=1
        #print ("ATTENTION CHECK: failed_nodes:" + str(failed_nodes) + " tried_attempts: " + str(tried_attempts) + "tried_trials" + str(tried_trials))
        print "ATTENTION: tried_attempts: " + str(tried_attempts)
        print "ATTENTION: self.Percent_attention_trials: " + str(self.Percent_attention_trials)
        print "ATTENTION: tried_trials: " + str(tried_trials)

        if (tried_attempts*100>self.Percent_attention_trials*tried_trials):
            print "ATTENTION: failed attention test 1"
            return False
 #       failed_nodes=len(Node.query.filter_by(failed=True,participant_id=participant.id).all())
        print "ATTENTION: passed attention test 1"
        print "ATTENTION: failed_nodes: " + str(failed_nodes)
        print "ATTENTION: Percent_failed_nodes: " + str(self.Percent_failed_nodes)
        print "ATTENTION: len(nodes): " + str(len(nodes))

        #note that this should only apply when you have enought trials this is why tried_trials is suppose to be large (e.g >4)
        if ((100*failed_nodes>self.Percent_failed_nodes*len(nodes))):
            print "ATTENTION: failed attention test 2"
            return False
        print "ATTENTION: passed attention test (all)"
        return True
########################### NORIHERE ################################

########################### NORIHERE ################################
class VisionInfo(Info):

    __mapper_args__ = {"polymorphic_identity": "vision_info"}

    @hybrid_property
    def seed(self):
        try:
            val=str(self.property1)
        except:
            val=self.property1
        return val

    @seed.setter
    def seed(self, my_seed):
        self.property1 = repr(my_seed)

    @seed.expression
    def seed(self):
        return repr(self.property1)



    @hybrid_property
    def reaction_time(self):
        return float(self.property2)

    @reaction_time.setter
    def reaction_time(self, my_RT):
        self.property2 = repr(my_RT)

    @reaction_time.expression
    def reaction_time(self):
        return cast(self.property2, Float)



    @hybrid_property
    def generation(self):
        if self.property5:
            return int(self.property3)
        else:
            return 0

    @generation.setter
    def generation(self, my_generation):
        self.property3 = repr(my_generation)

    @generation.expression
    def generation(self):
        return cast(self.property3, Integer)




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

    def add_node(self, newcomer):
        super(MultiChain, self).add_node(newcomer)
        prev_agents = type(newcomer).query\
                .filter_by(failed=False,
                           network_id=self.id,
                           )\
                .all()

        if prev_agents:
            previous_generation=max([p.generation for p in prev_agents]) + 1

        else:
            previous_generation=0
        newcomer.generation = previous_generation
        #newcomer.neighbors(direction="from")[0].transmit()
        # print newcomer.neighbors(direction="from")
        # print "DEBUG HERE (2)"
        # newcomer.receive()
        # print "DEBUG HERE (3)"

class VisionSource(Source):
    """ A source that initializes the pattern of the first generation """

    @hybrid_property
    def seed(self):
        try:
            val=str(self.property1)
        except:
            val=self.property1
        return val

    @seed.setter
    def seed(self, my_seed):
        self.property1 = repr(my_seed)

    @seed.expression
    def seed(self):
        return repr(self.property1)



    @hybrid_property
    def reaction_time(self):
        return float(self.property2)

    @reaction_time.setter
    def reaction_time(self, my_RT):
        self.property2 = repr(my_RT)

    @reaction_time.expression
    def reaction_time(self):
        return cast(self.property2, Float)



    @hybrid_property
    def generation(self):
        if self.property5:
            return int(self.property3)
        else:
            return 0

    @generation.setter
    def generation(self, my_generation):
        self.property3 = repr(my_generation)

    @generation.expression
    def generation(self):
        return cast(self.property3, Integer)


    __mapper_args__ = {"polymorphic_identity": "vision_source"}

    def _what(self):
        return VisionInfo

    def create_pattern(self, params):
        #VisionInfo(origin=self, contents=random.randint(0,100));
        mydimensions=len(params['range_min'])
        assert(mydimensions==params['my_dimensions'])
        range_max=params['range_max']
        range_min=params['range_min']
#        percision=params['percision']
        percision=4

        assert(len(range_max)==len(range_min))

        seed=[]
        for i in range(mydimensions):
            seed.append(round(random.random()*(range_max[i]-range_min[i])+range_min[i],percision))

        print "creating seed: {}".format(seed)
        assert(len(seed)==mydimensions)

        VisionInfo(origin=self, contents=str(seed))
        return str(seed)


class VisionAgent(Agent):
    def fail(self, vectors=True, infos=True, transmissions=True, transformations=True):
        """
        Fail a node, setting its status to "failed".

        Also fails all vectors that connect to or from the node.
        You cannot fail a node that has already failed, but you
        can fail a dead node.
        """



        if self.failed is True:
            #raise AttributeError(
            print " Warning: Cannot fail {} - it has already failed.".format(self)
        else:
            self.failed = True
            self.time_of_death = datetime.now()
            for n in self.neighbors(): ##
                n.fail()
                self.network.open= False

            if self.network is not None:
                self.network.calculate_full()

            if vectors:
                for v in self.vectors():
                    v.fail()
            if infos:
                for i in self.infos():
                    i.fail()
            if transmissions:
                for t in self.transmissions(direction="all"):
                    t.fail()
            if transformations:
                for t in self.transformations():
                    t.fail()

        self.network.open= True #because the network might be stuck

    """ A source that initializes the pattern of the first generation """
    @hybrid_property
    def generation(self):
        if not self.property1:
            return 0
        return int(self.property1)

    @generation.setter
    def generation(self, generation):
        self.property1 = repr(generation)

    @generation.expression
    def generation(self):
        return cast(self.property1, Integer)

    __mapper_args__ = {"polymorphic_identity": "vision_agent"}

    def _what(self):
        return VisionInfo

extra_routes = Blueprint(
    'extra_routes', __name__,
    template_folder='templates',
    static_folder='static')

@extra_routes.route("/get_trial_params/<int:node_id>/<int:participant_id>", methods=["GET"])
def get_trial_params(node_id,participant_id):
    exp = VisionGame(db.session)
    node = Node.query.get(node_id)
    #node = VisionAgent.query.get(node_id)

    #nodes = VisionAgent.query.filter_by(participant_id=participant_id, failed=False).all()
    #the_nodes = [n for n in nodes if n.id==node_id]
    print "--------##-------"
    print node
    print "--------##-------"

    #node=the_nodes[0]
    #net=node.network_id
    #net=Network.query.get(network_id)

    participants = Participant.query.filter_by(id=participant_id).all()
    participant=participants[0]
    bonus=exp.bonus(participants[0])
    exp.log("/get_trial_params: node_id: {} participant_id:{}".format(node_id,participant_id))
    # return the data

    target_src = "https://s3.amazonaws.com/thomas-nori-projects/dot.png"
    bcgrd_src = "https://s3.amazonaws.com/thomas-nori-projects/Circle.png"
    pres_time = 3000
    fix_time = 1000
    margin_error_x = 0.05
    margin_error_y = 0.05
    delta_x = 0.0
    delta_y = 0.0

    raw_data=dict()
    raw_data['target_src']=target_src
    raw_data['bcgrd_src']=bcgrd_src
    raw_data['pres_time']=pres_time
    raw_data['margin_error_x']=margin_error_x
    raw_data['margin_error_y']=margin_error_y
    raw_data['delta_x']=delta_x
    raw_data['delta_y']=delta_y


    data = dumps(raw_data)
    print "debug-----------\n----------\n"
    print node
    print "debug-----------\n----------\n"
    data = {"status": "success", "trial_params": data, "generation": node.generation}
    js = dumps(data, default=date_handler)
    return Response(js, status=200, mimetype='application/json')



# @extra_routes.route("/is_practice/<int:network_id>", methods=["GET"])
# def get_is_practice(network_id):
# #    exp = VisionGame(db.session)
#     net=Network.query.get(network_id)
#     data = {"status": "success", "is_practice": net.role == "practice"}
#     return Response(dumps(data), status=200, mimetype='application/json')


# @extra_routes.route("/trial_number_string/<int:node_id>/<int:participant_id>", methods=["GET"])
# def get_trial_number_string(node_id,participant_id):
#     exp = VisionGame(db.session)
#     node = LineAgent.query.get(node_id)
#     participants = Participant.query.filter_by(id=participant_id).all()
#     bonus=exp.bonus(participants[0])

#     exp.log("/trial_number_string GET request. Params: node_id: {}."
#             .format(node_id))

#     # check the node exists for the current particiapnt
#     nodes = len(LineAgent.query.filter_by(participant_id=node.participant_id).all())
#     all_trials=exp.K_all_trials

#     if node is None:
#         exp.log("Error: /trial_number_string/{}, node {} does not exist".format(node_id, node_id))
#         page = error_page(error_type="/trial_number_string, node does not exist")
#         js = dumps({"status": "error", "html": page})
#         return Response(js, status=400, mimetype='application/json')

#     # return the data
#     data = str(nodes) + " / " + str(all_trials) + ". Estimated bonus so far: " + str(bonus) + "$"
#     data = {"status": "success", "trial_str": data, "generation": node.generation}
#     exp.log("/trial_number_string GET request successful.")
#     js = dumps(data, default=date_handler)
#     return Response(js, status=200, mimetype='application/json')



def date_handler(obj):
    """Serialize dates."""
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj
