# to run offline yu do "nosetests -x --nocapture"
from __future__ import print_function
import sys
import numpy
from wallace import db
from wallace.nodes import Agent, Source
from wallace.information import Gene
from wallace.transformations import Mutation
from wallace import models
from experiment import LineGame, LineInfo, LineAgent, LineSource
from wallace.models import Node, Info
import random
import traceback
from datetime import datetime, date, timedelta
from dateutil import parser
from json import dumps

import subprocess
import re
import requests
import threading
import time



def timenow():
    """A string representing the current date and time."""
    return datetime.now()


class TestBandits(object):

    # run the tests online?
    sandbox = False

    if sandbox:
        # # how many bots to simulate?
        autobots = 20

        # # deploy to the sanbox
        # sandbox_output = subprocess.check_output(
        #     "wallace sandbox",
        #     shell=True)

        # m = re.search('Running as experiment (.*)...', sandbox_output)
        # exp_id = m.group(1)
        # url = "http://" + exp_id + ".herokuapp.com"

        # # Open the logs in the browser.
        # subprocess.call(
        #     "wallace logs --app " + exp_id,
        #     shell=True)

        # # code that each bot runs
        # def autobot(session, url, i):

        #     # manually added delay to space bots out
        #     time.sleep(i*2)
        #     print("bot {} starting".format(i))
        #     start_time = timenow()

        #     # generate a new id
        #     my_id = str(i) + ':' + str(i)
        #     current_trial = 0

        #     headers = {
        #         'User-Agent': 'python',
        #         'Content-Type': 'application/x-www-form-urlencoded',
        #     }

        #     # send AssignmentAccepted notification
        #     args = {
        #         'Event.1.EventType': 'AssignmentAccepted',
        #         'Event.1.AssignmentId': i
        #     }
        #     session.post(url + '/notifications', data=args, headers=headers)

        #     # create participant
        #     args = {'hitId': 'rogers-test-hit', 'assignmentId': i, 'workerId': i, 'mode': 'sandbox'}
        #     session.get(url + '/consent', params=args, headers=headers)
        #     session.post(url + "/participant/" + str(i) + '/' + str(i) + '/' + str(i))
        #     session.get(url + '/instructions/1', params=args, headers=headers)
        #     session.get(url + '/instructions/2', params=args, headers=headers)
        #     session.get(url + '/instructions/3', params=args, headers=headers)
        #     session.get(url + '/instructions/4', params=args, headers=headers)
        #     bah = session.get(url + '/num_trials', headers=headers)
        #     trials_per_network = bah.json()['n_trials']
        #     session.get(url + '/instructions/5', params=args, headers=headers)
        #     session.get(url + '/stage', params=args, headers=headers)

        #     # work through the trials
        #     working = True
        #     while working is True:
        #         try:
        #             # create_agent()
        #             agent = session.post(url + '/node/' + my_id, headers=headers)

        #             working = agent.status_code == 200
        #             if working is True:
        #                 agent_id = agent.json()['node']['id']
        #                 network_id = agent.json()['node']['network_id']
        #                 current_trial = 0
        #                 bandit_memory = []

        #                 # get_genes()
        #                 args = {"info_type": "Gene"}
        #                 infos = session.get(url + '/node/' + str(agent_id) + '/infos', headers=headers, params=args).json()['infos']
        #                 for info in infos:
        #                     if info['type'] == "memory_gene":
        #                         my_memory = int(info['contents'])
        #                     if info['type'] == "curiosity_gene":
        #                         my_curiosity = int(info['contents'])

        #                 # get_num_bandits()
        #                 num_bandits = session.get(url + '/num_bandits', headers=headers).json()['num_bandits']

        #                 for trial in range(trials_per_network):

        #                     # pick_a_bandit()
        #                     current_bandit = int(random.random()*num_bandits)
        #                     if my_memory > 0:
        #                         remember_bandit = current_bandit in bandit_memory[-my_memory:]
        #                     else:
        #                         remember_bandit = False
        #                     if remember_bandit:
        #                         remember_bandit = "true"
        #                     else:
        #                         remember_bandit = "false"

        #                     # get_num_tiles()
        #                     num_tiles = session.get(url + '/num_arms/' + str(network_id) + '/' + str(current_bandit), headers=headers).json()['num_arms']

        #                     # get_treasure_tile()
        #                     treasure_tile = session.get(url + '/good_arm/' + str(network_id) + '/' + str(current_bandit), headers=headers).json()['good_arm']

        #                     # prepare_for_trial
        #                     current_trial += 1

        #                     tiles_to_check = []
        #                     if remember_bandit == "false":
        #                         # check tiles
        #                         tiles_to_check = random.sample(range(1, num_tiles+1), my_curiosity)
        #                         for t in tiles_to_check:
        #                             data = {
        #                                 "contents": t,
        #                                 "info_type": "Pull",
        #                                 "property1": "true",
        #                                 "property2": current_bandit,
        #                                 "property3": remember_bandit,
        #                                 "property5": current_trial
        #                             }
        #                             session.post(url + '/info/' + str(agent_id), headers=headers, data=data)

        #                     # make final decision
        #                     if treasure_tile in tiles_to_check:
        #                         final_choice = treasure_tile
        #                     else:
        #                         final_choice = random.sample(range(1, num_tiles+1), 1)[0]
        #                     data = {
        #                         "contents": final_choice,
        #                         "info_type": "Pull",
        #                         "property1": "false",
        #                         "property2": current_bandit,
        #                         "property3": remember_bandit,
        #                         "property5": current_trial
        #                     }
        #                     session.post(url + '/info/' + str(agent_id), headers=headers, data=data)

        #                 # calculate fitness
        #                 session.get(url + '/node/' + str(agent_id) + '/calculate_fitness')
        #         except:
        #             working = False
        #             print("critical error for bot {}".format(i))
        #             print("bot {} is on trial {}".format(i, current_trial))
        #             traceback.print_exc()

        #     # go to debrief
        #     args = {'hitId': 'rogers-test-hit', 'assignmentId': i, 'workerId': i, 'mode': 'sandbox'}
        #     session.get(url + '/debrief/1', params=args, headers=headers)

        #     # send AssignmentSubmitted notification
        #     args = {
        #         'Event.1.EventType': 'AssignmentSubmitted',
        #         'Event.1.AssignmentId': i
        #     }
        #     session.post(url + '/notifications', data=args, headers=headers)

        #     stop_time = timenow()
        #     print("Bot {} finished in {}".format(i, stop_time - start_time))
        #     return

        # print("countdown before starting bots...")
        # time.sleep(20)
        # print("buffer ended, bots started")

        # # create worker threads
        # threads = []
        # for i in range(autobots):
        #     with requests.Session() as session:
        #         t = threading.Thread(target=autobot, args=(session, url, i,))
        #         threads.append(t)
        #         t.start()

    else:
        # do offline testing

        def test_run_linegame(self):

            """
            SIMULATE THE BANDIT GAME
            """

            self.db = db.init_db(drop_all=True) #this line is important for setup

            hit_id = str(random.random())
            overall_start_time = timenow()

            print("Running simulated experiment...", end="\r")
            sys.stdout.flush()

            # initialize the experiment
            exp_setup_start = timenow()
            exp = LineGame(self.db)
            exp_setup_stop = timenow()

            # reload it for timing purposes
            exp_setup_start2 = timenow()
            exp = LineGame(self.db)
            exp_setup_stop2 = timenow()

            # variables to store timing data
            p_ids = []
            p_times = []
            dum = timenow()
            assign_time = dum - dum
            process_time = dum - dum
            bonus=0

            num_completed_participants = 0

            # while there is space
            while exp.networks(full=False, role="experiment"):

                chain_lengths = [n.size(type=LineAgent) for n in exp.networks()]

                # update the print out
                chain_dic = dict([(n.id,n.size(type=LineAgent)) for n in exp.networks()])
                chain_list= [ chain_dic[k] for k in chain_dic.keys()]
                print("*******")
                print(chain_list)
                print("*******")

                if p_times:
                    print("Running simulated experiment... participant {} bonus {}, sum of chain length {}, {} nodes failed. Shortest chain: {}, longest chain: {}. Prev time: {}".format(
                        num_completed_participants+1,
                        bonus,
                        sum(chain_lengths),
                        len(Node.query.filter_by(failed=True).all()),
                        min(chain_lengths),
                        max(chain_lengths),
                        p_times[-1]),
                        end="\r")
                else:
                    print("Running simulated experiment... participant {} bonus {}, sum of chain length {}, {} nodes failed. Shortest chain: {}, longest chain: {}.".format(
                        num_completed_participants+1,
                        bonus,
                        sum(chain_lengths),
                        len(Node.query.filter_by(failed=True).all()),
                        min(chain_lengths),
                        max(chain_lengths)),
                        end="\r")
                sys.stdout.flush()

                # generate a new participant
                worker_id = str(random.random())
                assignment_id = str(random.random())
                from psiturk.models import Participant
                p = Participant(workerid=worker_id, assignmentid=assignment_id, hitid=hit_id)
                self.db.add(p)
                self.db.commit()
                p_id = p.uniqueid
                p_ids.append(p_id)
                p_start_time = timenow()

                # apply for new nodes
                while True:
                    assign_start_time = timenow()
                    # get a network
                    network = exp.get_network_for_participant(participant_id=p_id)
                    if network is None:
                        break
                    else:
                        # make a node
                        agent = exp.make_node_for_participant(
                            participant_id=p_id,
                            network=network)
                        # add it to the network
                        exp.add_node_to_network(
                            participant_id=p_id,
                            node=agent,
                            network=network)
                        exp.node_post_request(participant_id=p_id, node=agent)
                        self.db.commit()
                        assign_stop_time = timenow()
                        assign_time += (assign_stop_time - assign_start_time)

                        # play the experiment
                        process_start_time = timenow()

                        # get their true ratio
                        TrueRatio = int(agent.received_infos()[0].contents)
                        #print(agent.received_infos()[0].generation)
                        generation = int(agent.received_infos()[0].generation)


                        ResponseRatio = int(TrueRatio + round(5*numpy.random.normal()))
                        ResponseRatio = max(min (ResponseRatio,100), 0)

                        if (abs(ResponseRatio-TrueRatio)>=exp.UI_PROX_T):
                            ResponseRatio='NaN'


                        p_wrong=0.1
                        if random.random() < p_wrong:
                            ResponseRatio='NaN'


                        p_more_trials=0.1
                        p_more_mistakes=0.5

                        num_attempts=1
                        reaction_time=random.random()*1000
                        true_seed=TrueRatio
                        result_list=repr([ResponseRatio])

                        #simulate multiple trials
                        if unicode(ResponseRatio).isnumeric():
                            if random.random() < p_more_trials:
                                num_attempts+=1
                                result_list=str([ResponseRatio,100-ResponseRatio])
                                if random.random() < p_more_mistakes:
                                    num_attempts+=1
                                    result_list=([ResponseRatio,100-ResponseRatio,100-TrueRatio])
                                    if random.random() < p_more_mistakes:
                                        num_attempts+=1
                                        result_list=([100-TrueRatio,100-TrueRatio,100-TrueRatio])
                                        ResponseRatio='NaN'

                        info = LineInfo(contents=ResponseRatio, origin=agent)

                        info.num_attempts=num_attempts
                        info.reaction_time=reaction_time
                        info.true_seed=true_seed
                        info.result_list=result_list
                        #info.generation=generation+1
                        info.generation=agent.generation


                        # prob of 'Nan', prob wierd number, prob of right number
                        # get all bandits
                        exp.info_post_request(node=agent, info=info)
                        self.db.commit()
                        process_stop_time = timenow()
                        process_time += (process_stop_time - process_start_time)

                worked = exp.data_check(participant=p)
                assert worked
                bonus = exp.bonus(participant=p)
                p.bonus=bonus
                assert bonus >= 0*exp.bonus_payment
                assert bonus <= 1*exp.bonus_payment
                attended = exp.attention_check(participant=p)
                if not attended:

                    participant_nodes = models.Node.query\
                        .filter_by(participant_id=p_id, failed=False)\
                        .all()
                    p.status = 102

                    for node in participant_nodes:
                        node.fail()

                    self.db.commit()
                else:
                    p.status = 101
                    self.db.commit()
                    exp.submission_successful(participant=p)
                    self.db.commit()

                p_stop_time = timenow()
                num_completed_participants += 1
                p_times.append(p_stop_time - p_start_time)

            print("Running simulated experiment...      done!                                      ")
            sys.stdout.flush()

            overall_stop_time = timenow()

            assert len(exp.networks()) == exp.practice_repeats + exp.experiment_repeats

            """
            TEST NODES
            """

            print("Testing nodes...", end="\r")
            sys.stdout.flush()

            for network in exp.networks(role="experiment"):

                 agents = network.nodes(type=LineAgent)
                 assert len(agents) == network.max_size
                 sources = network.nodes(type=LineSource)
                 assert len(sources) == 1 # only one source for every network


            print("Testing nodes...                     done!")
            sys.stdout.flush()

            """
            TEST VECTORS
            """

            print("Testing vectors...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=LineAgent)
                vectors = network.vectors()
                source = network.nodes(type=LineSource)[0]


                for agent in agents:
                    incomes=[v for v in vectors if v.destination_id == agent.id] #incomes=agent.vectors(direction="incoming")
                    fromes=[v for v in vectors if v.origin_id == agent.id] #fromes=agent.vectors(direction="outgoing")
                    assert len(incomes) == 1
                    assert len(fromes) in [0, 1]

                if network.role == "experiment":
                    assert len([v for v in vectors if v.origin_id == source.id]) == 1

            print("Testing vectors...                   done!")
            sys.stdout.flush()

            """
            TEST INFOS
            """

            print("Testing infos...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=LineAgent)
                source = network.nodes(type=LineSource)[0]
                assert len(source.infos(LineInfo)) == 1

                for agent in agents:
                    infos =  agent.infos(LineInfo)
                    assert len(infos) == 1
                    info=infos[0]
                    true_seed=info.true_seed
                    try:
                        contents=int(info.contents)
                    except:
                        assert (contents=='NaN')
                    else:
                        assert (abs(contents-true_seed)<exp.UI_PROX_T)


            print("Testing infos...                     done!")
            sys.stdout.flush()

            """
            TEST TRANSMISSIONS
            """

            print("Testing transmissions...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=LineAgent)
                source = network.nodes(type=LineSource)[0]
                infos = network.infos(LineInfo)

                assert len(source.transmissions(direction="all", status="pending")) == 0
                assert len(source.transmissions(direction="incoming", status="all")) == 0
                if agents:
                    assert len(source.transmissions(direction="outgoing", status="received")) == 1
                else:
                    assert len(source.transmissions(direction="outgoing", status="received")) == 0

                for agent in agents:
                     assert len(agent.transmissions(direction="all", status="pending")) == 0
                     assert len(agent.transmissions(direction="incoming", status="received")) == 1
                     assert len(agent.transmissions(direction="outgoing", status="received"))  in [0, 1]

            #         if agent.generation == exp.generations-1:
            #             assert len(agent.transmissions(direction="outgoing", status="received")) == 0

            print("Testing transmissions...             done!")


            print("Print contents. <<<<<<<<<<<<<<<<<<<<<<<<")
            number_of_participants_to_check=3
            print ("Print contents of {} last particiapnts...".format(number_of_participants_to_check))
            networks = exp.networks()
            my_part_id=None
            for network in networks:
                agents=network.nodes(type=LineAgent)
                for agent in agents:
                    my_part_id = agent.participant_id
                    if not(my_part_id==None):
                        break

            participants = Participant.query.filter_by(uniqueid=my_part_id).all()
            print(participants)
            print('myhitid:' + my_part_id)
            my_hit_id=participants[0].hitid
            print('myhitid:' + my_part_id)


            # for network in networks:
            #     agents = network.nodes(type=LineAgent)
            #     if agents:
            #         hit_ids=[agent.participant_id for agent in agents]
            #     else:
            #         hit_ids=None
            #     print(hit_ids)


            # print(hit_ids)
            # hit_id=hit_ids[0]
            participants = Participant.query.filter_by(hitid=my_hit_id).all()
            #    participants = Participant.query.all(assignment_id=assignment_id)
            dates={p.beginhit:p for p in participants}
            sorted_dates_tuples=sorted(dates.items())

            # check that number_of_participants_to_check
            if number_of_participants_to_check in [0,None]:
                number_of_participants_to_check= len(sorted_dates_tuples)
            my_num_parts= min ([number_of_participants_to_check, len(sorted_dates_tuples)])

            selected_participants_ids=[k[1].uniqueid for k in sorted_dates_tuples[(-my_num_parts):]]

            #print(selected_participants_ids)
            #nodes(self, type=None, failed=False, participant_id=None):

    #         print("Testing infos...", end="\r")
    #            sys.stdout.flush()

            for network in networks:
                print(network)
                agents = network.nodes(type=LineAgent)
                relevant_agents = [agent for agent in agents if agent.participant_id in selected_participants_ids]
                if not(relevant_agents): # if this network do not touch the list of particiapnts
                    continue
                source = network.nodes(type=LineSource)[0]

                for agent in agents:
                    infos =  agent.infos(Info)
                    for info in infos:
                        try:
                            true_seed=info.true_seed
                            try:
                                contents=int(info.contents)
                                is_fail=False
                            except:
                                contents==None
                                is_fail=True
                        except:
                            contents=None
                            true_seed=None
                            is_fail=True

                        net_role=network.role
                        net_id=network.id
                        part_id=agent.participant_id
                        target=contents
                        source=true_seed
                        summary={"net_role": net_role, "net_id": net_id, "is_fail": is_fail, "target": target, "source": source}
                        #print(summary)
                        str_summary="net_role: {} net_id: {} is_fail: {} part_id: {} target: {} source: {}".format(net_role,net_id,is_fail,part_id,target,source)
                        print(str_summary)

                chain_lengths = [n.size(type=LineAgent) for n in exp.networks()]
                chain_dic = dict([(n.id,n.size(type=LineAgent)) for n in exp.networks()])
                chain_list= [ chain_dic[k] for k in chain_dic.keys()]
                selected_participants_bonus=sum([k[1].bonus for k in sorted_dates_tuples[(-my_num_parts):]])
                all_participants_bonus=sum([k[1].bonus for k in sorted_dates_tuples])

                all_chain_length=sum(chain_lengths)
                min_chain_length=min(chain_lengths)
                max_chain_length=max(chain_lengths)
                num_failed_nodes=len(Node.query.filter_by(failed=True).all())
                selected_participants_num=len(selected_participants_ids)

                str_general_summary="all_bonus={} selected_part_num={} part_bonus={} all_chain_length={} max_chain_length={} min_chain_length={} num_failed_nodes={}".format(all_participants_bonus, selected_participants_num, selected_participants_bonus, all_chain_length, max_chain_length, min_chain_length, num_failed_nodes)
                summary_general={"all_bonus": all_participants_bonus, "selected_part_num": selected_participants_num, "selected_part_bonus": selected_participants_bonus, "all_chain_length": all_chain_length, "max_chain_length":max_chain_length, "min_chain_length": min_chain_length, "num_failed_nodes": num_failed_nodes, "all_chain_lengths": str(chain_list)}
                print(str_general_summary)
                print(summary_general)


            print("TEST DICTIONARIES!!! ")
            number_of_current_participants=1;
            number_of_participants_to_check=0;

            participants = Participant.query.filter_by(hitid=my_hit_id).all()

            dates={p.beginhit:p for p in participants}
            sorted_dates_tuples=sorted(dates.items())

            # check that number_of_participants_to_check
            if number_of_participants_to_check==0:
                number_of_participants_to_check= len(sorted_dates_tuples)
            my_num_parts= min ([number_of_participants_to_check, len(sorted_dates_tuples)])
            number_of_current_participants=min([number_of_current_participants,my_num_parts])

            selected_participants_ids=[k[1].uniqueid for k in sorted_dates_tuples[(-my_num_parts):]]
            current_participants_ids=[k[1].uniqueid for k in sorted_dates_tuples[(-number_of_current_participants):]]



            summary_node_list=[]
            summary_node_dict={}
            summary_node_dict_fail=dict([(p,{}) for p in selected_participants_ids])

            for network in networks:
                agents = network.nodes(type=LineAgent)
                relevant_agents = [agent for agent in agents if agent.participant_id in selected_participants_ids]
                if not(relevant_agents): # if this network do not touch the list of particiapnts
                    continue

                summary_node_dict[network.id]={}
                summary_node_dict[network.id]['label']=network.id
                summary_node_dict[network.id]['role']=network.role
                summary_node_dict[network.id]['current']=False
                if network.role == "experiment":
                    summary_node_dict[network.id]['x']=[-1] * (exp.M_length + 1)
                    summary_node_dict[network.id]['y']=[-1] * (exp.M_length + 1)
                else:
                    summary_node_dict[network.id]['x']=[-1] * (max_chain_length + 1)
                    summary_node_dict[network.id]['y']=[-1] * (max_chain_length + 1)

                #print('summary_node_dict at initialization')
                #print (summary_node_dict)
                #source = network.nodes(type=LineSource)[0]
                #print("relevant network")
                #print(network)
                for agent in agents:
                    agent_p_id=agent.participant_id
                    if agent_p_id in current_participants_ids:
                        summary_node_dict[network.id]['label']=str(network.id) + "|" + str(agent_p_id)
                        summary_node_dict[network.id]['current']=True


                    #print("-->relevant agent")
                    #print(agent)
                    infos =  agent.infos()
                    #infos = Info.query.filter_by(origin_id=agent.id).all()
                    #print("---->>relevant infos")
                    #print(infos)
                    #print(LineInfo.query.filter_by(origin_id=agent.id).all())
                    for info in infos:

                        #print("---->>>>relevant info")
                        #print(info)
                        #print(">>>>>>>>info true seed:")
                        #print(info.true_seed)
                        is_fail=info.failed
                        generation=info.generation
                        try:

                            true_seed=info.true_seed
                            try:
                                contents=int(info.contents)
                            except:
                                contents==0
                                is_fail=True
                        except:
                            contents=None
                            true_seed=-10
                            is_fail=True
                            generation=0
                        #print("---->>here")

                        net_role=network.role
                        net_id=network.id
                        part_id=agent.participant_id
                        target=contents
                        value_source=true_seed
                        summary_node={"net_role": net_role, "net_id": net_id, "is_fail": is_fail, "target": target, "source": value_source}
                        #print(summary_node)
                        str_summary="net_role: {} net_id: {} is_fail: {} part_id: {} target: {} source: {}".format(net_role,net_id,is_fail,part_id,target,value_source)
                        print("is_fail:"+ str(is_fail) + " contents:" + str(contents) )
                        if is_fail:
                            assert(not(is_fail))
                            # if agent_p_id in current_participants_ids:
                            #     gen = 1.0*(max([generation-1, 0])) + 0.8*random.random()
                            #     summary_node_dict_fail[agent_p_id]['x'].append(gen)
                            #     summary_node_dict_fail[agent_p_id]['y'].append(true_seed)
                        else:
                            gen = 1.0*(generation) + 0.8*random.random()
                            gen = generation

                            #print("generation=" + str(generation) + " gen=" + str(gen))
                            summary_node_dict[network.id]['x'][generation]=gen
                            summary_node_dict[network.id]['y'][generation]=target


                            if generation==1:
                               gen=1.0*(0)+0.8*random.random()
                               gen = 0
                               summary_node_dict[network.id]['x'][0]=gen
                               summary_node_dict[network.id]['y'][0]=value_source

                agents = Node.query.filter_by(failed=True, network_id=network.id).all()
                for agent in agents:
                    agent_p_id=agent.participant_id
                    if agent_p_id in selected_participants_ids:
                        if not(summary_node_dict_fail[agent_p_id]):
                            summary_node_dict_fail[agent_p_id]['label']=agent_p_id
                            summary_node_dict_fail[agent_p_id]['current']=False
                            summary_node_dict_fail[agent_p_id]['x']=[]
                            summary_node_dict_fail[agent_p_id]['y']=[]
                            summary_node_dict_fail[agent_p_id]['role']=[]

                        generation = agent.generation
                        true_seed = info.true_seed
                        gen = max([generation-1, 0])
                        print("*****")
                        print(agent)
                        print("gen:"+ str(generation) + " true_seed:" + str(true_seed) + "failed:" + str(agent.failed))
                        if network.role=="experiment":
                            assert(generation<=exp.M_length)

                        if (gen and true_seed):
                            summary_node_dict_fail[agent_p_id]['x'].append(gen)
                            summary_node_dict_fail[agent_p_id]['y'].append(true_seed)
                            summary_node_dict_fail[agent_p_id]['role'].append("e" if network.role=="experiment" else "p")
                            #print('summary_node_dict_fail at initialization')
                            #print (summary_node_dict_fail)

                    if agent_p_id in current_participants_ids:
                        summary_node_dict_fail[agent_p_id]['label']=str(agent_p_id)+ "<" + str(network.id)
                        summary_node_dict_fail[agent_p_id]['current']=True


            print('****> summary_node_dict final')
            print (dumps(summary_node_dict))
            print('****> summary_node_dict_fail final')
            print (dumps(summary_node_dict_fail))

#             print('****> summary_node_dict_fail prooned')
# #            summary_node_dict_fail={k: summary_node_dict_fail[k] for k in summary_node_dict_fail.keys() if len(summary_node_dict_fail[k]['x'])>0}
#             temp=[summary_node_dict_fail[k]['x'] for k in summary_node_dict_fail.keys()]
#             print(temp)
#             summary_node_dict_fail={k: summary_node_dict_fail[k] for k in summary_node_dict_fail.keys() if summary_node_dict_fail[k]['x']}

#             print (summary_node_dict_fail)

            """
            TEST TRANSFORMATIONS
            """

            print("Not testing transformations (there are none)...", end="\r")
            sys.stdout.flush()

            # for network in exp.networks():

            #     agents = network.nodes(type=Agent)
            #     genetic_source = network.nodes(type=GeneticSource)[0]
            #     infos = network.infos()

            #     assert len(genetic_source.transformations()) == 0

            #     for agent in agents:
            #         ts = agent.transformations()
            #         assert len(ts) == 2
            #         for t in ts:
            #             assert isinstance(t, Mutation)

            print("Testing transformations (did nothing)...           done!")

            """
            TEST FITNESS
            """

            # print("Testing fitness...", end="\r")
            # sys.stdout.flush()

            # for network in exp.networks():

            #     agents = network.nodes(type=Agent)
            #     sources = network.nodes(type=GeneticSource)

            #     for agent in agents:
            #         assert isinstance(agent.fitness, float)

            #     for source in sources:
            #         assert not isinstance(source.property4, float)

            print("TODO:Testing fitness...                   done!")
            sys.stdout.flush()

            print("All tests passed: good job!")

            print("Timings:")
            overall_time = overall_stop_time - overall_start_time
            print("Overall time to simulate experiment: {}".format(overall_time))
            setup_time = exp_setup_stop - exp_setup_start
            print("Experiment setup(): {}".format(setup_time))
            print("Experiment load: {}".format(exp_setup_stop2 - exp_setup_start2))
            print("Participant assignment: {}".format(assign_time))
            print("Participant processing: {}".format(process_time))
            # for i in range(len(p_times)):
            #     if i == 0:
            #         total_time = p_times[i]
            #     else:
            #         total_time += p_times[i]
            #     print("Participant {}: {}, total: {}".format(i, p_times[i], total_time))

            print("#########")

