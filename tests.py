from __future__ import print_function
import sys
from wallace import db
from wallace.nodes import Agent, Source
from wallace.information import Gene, Meme
from wallace import models
from experiment import CooperationGame, Decision, CooperationAgent, SummarySource, Summary
import random
import traceback
from datetime import datetime
import json
from json import dumps
import math

import subprocess
import re
import requests
import threading
import time


def timenow():
    """A string representing the current date and time."""
    return datetime.now()


class TestCooperation(object):

    sandbox = False

    if sandbox:

        autobots = 60

        sandbox_output = subprocess.check_output(
            "wallace sandbox",
            shell=True)

        m = re.search('Running as experiment (.*)...', sandbox_output)
        exp_id = m.group(1)
        url = "http://" + exp_id + ".herokuapp.com"

        # Open the logs in the browser.
        subprocess.call(
            "wallace logs --app " + exp_id,
            shell=True)

        # methods that defines the behavior of each worker
        def autobot(session, url, i):

            time.sleep(i*2)
            print("bot {} starting".format(i))
            start_time = timenow()

            my_id = str(i) + ':' + str(i)
            current_trial = 0

            headers = {
                'User-Agent': 'python',
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            # send AssignmentAccepted notification
            args = {
                'Event.1.EventType': 'AssignmentAccepted',
                'Event.1.AssignmentId': i
            }
            session.post(url + '/notifications', data=args, headers=headers)

            # create participant
            args = {'hitId': 'rogers-test-hit', 'assignmentId': i, 'workerId': i, 'mode': 'sandbox'}
            session.get(url + '/consent', params=args, headers=headers)
            session.post(url + "/participant/" + str(i) + '/' + str(i) + '/' + str(i))
            session.get(url + '/instructions/1', params=args, headers=headers)
            session.get(url + '/instructions/2', params=args, headers=headers)
            session.get(url + '/instructions/3', params=args, headers=headers)
            session.get(url + '/stage', params=args, headers=headers)

            # work through the trials
            working = True
            while working is True:
                current_trial += 1
                agent = None
                transmission = None
                information = None
                information2 = None
                information3 = None
                try:
                    agent = session.post(url + '/node/' + my_id, headers=headers)
                    working = agent.status_code == 200
                    if working is True:
                        agent_id = agent.json()['node']['id']
                        network_id = agent.json()['node']['network_id']
                        levels = int((session.get(url + '/levels/' + str(network_id), headers=headers)).json()['levels'])
                        for l in range(levels):
                            contents = str(int(round(random.random())))
                            args = {'info_type': 'Decision', 'contents': contents}
                            session.post(url + '/info/' + str(agent_id) + '/' + str(l + 1), data=args, headers=headers)

                except:
                    working = False
                    print("critical error for bot {}".format(i))
                    print("bot {} is on trial {}".format(i, current_trial))
                    print("bot {} agent request: {}".format(i, agent))
                    print("bot {} information request: {}".format(i, information))
                    print("bot {} transmission request: {}".format(i, transmission))
                    print("bot {} 2nd information request: {}".format(i, information2))
                    print("bot {} 3rd information request: {}".format(i, information3))
                    traceback.print_exc()

            # send AssignmentSubmitted notification
            args = {
                'Event.1.EventType': 'AssignmentSubmitted',
                'Event.1.AssignmentId': i
            }
            session.post(url + '/notifications', data=args, headers=headers)

            stop_time = timenow()
            print("Bot {} finished in {}".format(i, stop_time - start_time))
            return

        print("countdown before starting bots...")
        time.sleep(20)
        print("buffer ended, bots started")

        # create worker threads
        threads = []
        for i in range(autobots):
            with requests.Session() as session:
                t = threading.Thread(target=autobot, args=(session, url, i,))
                threads.append(t)
                t.start()

    else:

        def setup(self):
            self.db = db.init_db(drop_all=True)

        def teardown(self):
            self.db.rollback()
            self.db.close()

        def add(self, *args):
            self.db.add_all(args)
            self.db.commit()

        def test_run_cooperation(self):

            """
            SIMULATE THE COOPERATION GAME
            """

            hit_id = str(random.random())

            overall_start_time = timenow()

            print("Running simulated experiment...", end="\r")
            sys.stdout.flush()

            exp_setup_start = timenow()
            exp = CooperationGame(self.db)
            exp_setup_stop = timenow()

            exp_setup_start2 = timenow()
            exp = CooperationGame(self.db)
            exp_setup_stop2 = timenow()

            p_ids = []
            p_times = []
            dum = timenow()
            assign_time = dum - dum
            process_time = dum - dum

            while exp.networks(full=False):

                num_completed_participants = len(exp.networks()[0].nodes(type=Agent))

                if p_times:
                    print("Running simulated experiment... participant {} of {}, {} participants failed. Prev time: {}".format(
                        num_completed_participants+1,
                        exp.networks()[0].max_size,
                        len(exp.networks()[0].nodes(failed=True)),
                        p_times[-1]),
                        end="\r")
                else:
                    print("Running simulated experiment... participant {} of {}, {} participants failed.".format(
                        num_completed_participants+1,
                        exp.networks()[0].max_size,
                        len(exp.networks()[0].nodes(failed=True))),
                        end="\r")
                sys.stdout.flush()

                worker_id = str(random.random())
                assignment_id = str(random.random())
                from psiturk.models import Participant
                p = Participant(workerid=worker_id, assignmentid=assignment_id, hitid=hit_id)
                self.db.add(p)
                self.db.commit()
                p_id = p.uniqueid
                p_ids.append(p_id)
                p_start_time = timenow()

                while True:
                    assign_start_time = timenow()
                    network = exp.get_network_for_participant(participant_id=p_id)
                    if network is None:
                        break
                    else:
                        agent = exp.make_node_for_participant(
                            participant_id=p_id,
                            network=network)
                        exp.add_node_to_network(
                            participant_id=p_id,
                            node=agent,
                            network=network)
                        self.db.commit()
                        assign_stop_time = timenow()
                        assign_time += (assign_stop_time - assign_start_time)

                        process_start_time = timenow()
                        levels = agent.network.levels

                        for l in range(levels):
                            d = int(round(random.random()))
                            dec = Decision(origin=agent, contents=d)
                            dec.level = l+1
                        self.db.commit()
                        process_stop_time = timenow()
                        process_time += (process_stop_time - process_start_time)

                worked = exp.data_check(participant=p)
                assert worked
                bonus = exp.bonus(participant=p)
                assert bonus >= 0
                assert bonus <= 1
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

            for network in exp.networks():

                allowed_groups = range(int(math.ceil(network.generation_size/float(network.group_size))))

                agents = network.nodes(type=Agent)
                assert len(agents) == network.max_size
                for generation in range(network.generations):
                    assert len([a for a in agents if a.generation == generation]) == network.generation_size
                    for group in allowed_groups:
                        assert len([a for a in agents if a.generation == generation and a.group == group]) == network.group_size

                sources = network.nodes(type=Source)
                assert len(sources) == 1
                summary_source = network.nodes(type=SummarySource)
                assert len(summary_source) == 1

                summary_source = summary_source[0]

                vectors = network.vectors()

                for agent in agents:
                    assert type(agent) == CooperationAgent

                for agent in agents:
                    if agent.generation == 0:
                        assert len(agent.vectors(direction="incoming")) == 0
                    else:
                        assert len(agent.vectors(direction="incoming")) == 1
                        assert agent.is_connected(direction="from", whom=summary_source)
                        assert len(agent.neighbors(type=CooperationAgent, connection="from")) == 0

            print("Testing nodes...                     done!")
            sys.stdout.flush()

            """
            TEST VECTORS
            """

            print("Testing vectors...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=Agent)
                vectors = network.vectors()
                summary_source = network.nodes(type=SummarySource)[0]

                for v in vectors:
                    assert isinstance(v.origin, SummarySource)
                    assert v.origin == summary_source
                    assert isinstance(v.destination, CooperationAgent)

                for agent in agents:
                    if agent.generation == 0:
                        assert len(agent.vectors(direction="all")) == 0
                    else:
                        assert len(agent.vectors(direction="all")) == 1
                        assert len(models.Vector.query.filter_by(origin_id=summary_source.id, destination_id=agent.id).all()) == 1

            print("Testing vectors...                   done!")
            sys.stdout.flush()

            """
            TEST INFOS
            """

            print("Testing infos...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                num_groups = int(math.ceil(network.generation_size/float(network.group_size)))
                levels = network.levels

                agents = network.nodes(type=Agent)
                vectors = network.vectors()
                summary_source = network.nodes(type=SummarySource)[0]

                summaries = summary_source.infos()
                assert len(summaries) == num_groups*network.generations
                summaries = [s for s in summaries if isinstance(s, Summary)]
                assert len(summaries) == num_groups*network.generations

                for generation in range(network.generations):
                    for group in range(num_groups):
                        assert len([s for s in summaries if s.group == group and s.generation == generation]) == 1

                for agent in agents:

                    infos = agent.infos()
                    assert len(infos) == levels
                    for i in infos:
                        assert isinstance(i, Decision)

                    received_infos = agent.received_infos()
                    if agent.generation == 0:
                        assert len(received_infos) == 0
                    else:
                        assert len(received_infos) == 1

            print("Testing infos...                     done!")
            sys.stdout.flush()

            """
            TEST TRANSMISSIONS
            """

            print("Testing transmissions...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=Agent)
                vectors = network.vectors()
                summary_source = network.nodes(type=SummarySource)[0]
                infos = network.infos()

                for agent in agents:
                    pending_transmissions = agent.transmissions(direction="incoming", status="pending")
                    received_transmissions = agent.transmissions(direction="incoming", status="received")
                    assert len(pending_transmissions) == 0
                    if agent.generation == 0:
                        assert len(received_transmissions) == 0
                    else:
                        assert len(received_transmissions) == 1

                    if agent.generation > 0:
                        received_infos = agent.received_infos()
                        assert len(received_infos) == 1
                        received_info = received_infos[0]
                        assert isinstance(received_info, Summary)
                        assert received_info.generation == agent.generation - 1
                        assert received_info.group == agent.group
                    else:
                        assert len(agent.received_infos()) == 0

            print("Testing transmissions...             done!")

            """
            TEST FITNESS
            """

            print("Testing fitness...", end="\r")
            sys.stdout.flush()

            # agents = CooperationAgent.query.filter_by(network_id=2).all()
            # for a in agents:
            #     print("*****")
            #     print(a.generation)
            #     print(a.score)
            #     decisions = a.infos(type=Decision)
            #     print([d for d in decisions if d.level == 1][0].payoff)
            #     if len(decisions) > 1:
            #         print([d for d in decisions if d.level == 2][0].payoff)
            #     if len(decisions) > 2:
            #         print([d for d in decisions if d.level == 3][0].payoff)

            print("Testing fitness...                   SKIPPED - no tests.")
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
            for i in range(len(p_times)):
                if i == 0:
                    total_time = p_times[i]
                else:
                    total_time += p_times[i]
                print("Participant {}: {}, total: {}".format(i, p_times[i], total_time))

            print("#########")
            # test = [p.total_seconds() for p in p_times]
            # print(test)
