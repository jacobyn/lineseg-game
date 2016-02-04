from __future__ import print_function
import sys
from wallace import db
from wallace.nodes import Agent, Source
from wallace.information import Gene
from wallace.transformations import Mutation
from wallace import models
from experiment import BanditGame, MemoryGene, CuriosityGene, Pull, GeneticSource, Bandit, BanditAgent
import random
import traceback
from datetime import datetime

import subprocess
import re
import requests
import threading
import time


def timenow():
    """A string representing the current date and time."""
    return datetime.now()


class TestBandits(object):

    sandbox = True

    if sandbox:

        autobots = 1

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
            session.get(url + '/instructions/4', params=args, headers=headers)
            bah = session.get(url + '/num_trials', headers=headers)
            trials_per_network = bah.data.n_trials
            session.get(url + '/instructions/5', params=args, headers=headers)
            session.get(url + '/stage', params=args, headers=headers)

            # work through the trials
            working = True
            while working is True:
                agent = None
                transmission = None
                information = None
                information2 = None
                information3 = None
                try:
                    # create_agent()
                    agent = session.post(url + '/node/' + my_id, headers=headers)
                    working = agent.status_code == 200
                    if working is True:
                        agent_id = agent.json()['node']['id']
                        network_id = agent.json()['node']['network_id']
                        current_trial = 0
                        bandit_memory = []

                        # get_genes()
                        args = {"info_type": "Gene"}
                        infos = session.get(url + '/node/' + agent_id + '/infos', headers=headers, params=args).infos
                        for info in infos:
                            if info.type == "memory_gene":
                                my_memory = int(i.contents)
                            if info.type == "curiosity_gene":
                                my_curiosity = int(i.contents)

                        # get_num_bandits()
                        num_bandits = session.get(url + '/num_bandits', headers=headers).num_bandits

                        for trial in range(trials_per_network):

                            # pick_a_bandit()
                            current_bandit = int(random.random()*num_bandits)
                            if my_memory > 0:
                                remember_bandit = current_bandit in bandit_memory[-my_memory:]
                            else:
                                remember_bandit = False
                            if remember_bandit:
                                remember_bandit = "true"
                            else:
                                remember_bandit = "false"

                            # get_num_tiles()
                            num_tiles = session.get(url + '/num_arms/' + network_id + '/' + current_bandit, headers=headers).num_tiles

                            # get_treasure_tile()
                            treasure_tile = session.get(url + '/treasure_tile/' + network_id + '/' + current_bandit, headers=headers).treasure_tile

                            # prepare_for_trial
                            current_trial += 1

                            tiles_to_check = []
                            if remember_bandit == "false":
                                # check tiles
                                tiles_to_check = random.sample(range(1, num_tiles+1), my_curiosity)
                                for t in tiles_to_check:
                                    data = {
                                        "contents": t,
                                        "info_type": "Pull",
                                        "property1": "true",
                                        "property2": current_bandit,
                                        "property3": remember_bandit,
                                        "property5": current_trial
                                    }
                                    session.post(url + '/info/' + agent_id, headers=headers, data=data)

                            if treasure_tile in tiles_to_check:
                                final_choice = treasure_tile
                            else:
                                final_choice = random.sample(range(1, num_tiles+1), 1)[0]
                            data = {
                                "contents": final_choice,
                                "info_type": "Pull",
                                "property1": "false",
                                "property2": current_bandit,
                                "property3": remember_bandit,
                                "property5": current_trial
                            }
                            session.post(url + '/info/' + agent_id, headers=headers, data=data)

                        # calculate fitness
                        session.get(url + '/node/' + agent_id + '/calculate_fitness')
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

            # go to debrief
            args = {'hitId': 'rogers-test-hit', 'assignmentId': i, 'workerId': i, 'mode': 'sandbox'}
            session.get(url + '/debrief/1', params=args, headers=headers)

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

        def test_run_bandit(self):

            """
            SIMULATE THE BANDIT GAME
            """

            hit_id = str(random.random())

            overall_start_time = timenow()

            print("Running simulated experiment...", end="\r")
            sys.stdout.flush()

            exp_setup_start = timenow()
            exp = BanditGame(self.db)
            exp_setup_stop = timenow()

            exp_setup_start2 = timenow()
            exp = BanditGame(self.db)
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

                        memory = int(agent.infos(type=MemoryGene)[0].contents)
                        curiosity = int(agent.infos(type=CuriosityGene)[0].contents)
                        bandit_memory = []
                        for trial in range(exp.n_trials):
                            bandit_id = random.randint(0, exp.n_bandits-1)
                            if memory > 0:
                                remember_bandit = bandit_id in bandit_memory[-memory:]
                                if remember_bandit:
                                    remember_bandit = "true"
                                else:
                                    remember_bandit = "false"
                            else:
                                remember_bandit = "false"
                            if remember_bandit == "false":
                                vals = random.sample(range(1, exp.n_options + 1), curiosity)
                                for val in vals:
                                    pull = Pull(origin=agent, contents=val)
                                    pull.check = "true"
                                    pull.bandit_id = bandit_id
                                    pull.remembered = remember_bandit
                                    pull.trial = trial
                            pull = Pull(origin=agent, contents=random.randint(1, exp.n_options))
                            pull.check = "false"
                            pull.bandit_id = bandit_id
                            pull.remembered = remember_bandit
                            pull.trial = trial
                            bandit_memory.append(bandit_id)
                        self.db.commit()
                        agent.calculate_fitness()
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

                agents = network.nodes(type=Agent)
                assert len(agents) == network.max_size
                for generation in range(network.generations):
                    assert len([a for a in agents if a.generation == generation]) == network.generation_size

                sources = network.nodes(type=Source)
                assert len(sources) == 1 + exp.n_bandits
                genetic_source = network.nodes(type=GeneticSource)
                assert len(genetic_source) == 1
                bandits = network.nodes(type=Bandit)
                assert len(bandits) == exp.n_bandits

                genetic_source = genetic_source[0]

                for agent in agents:
                    assert type(agent) == BanditAgent

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
                genetic_source = network.nodes(type=GeneticSource)[0]

                for agent in agents:
                    if agent.generation == 0:
                        assert len(agent.vectors(direction="incoming")) == 1
                        assert agent.is_connected(direction="from", whom=genetic_source)
                    else:
                        assert len(agent.vectors(direction="incoming")) == 1
                        assert len(agent.neighbors(type=BanditAgent, connection="from")) == 1

                for v in vectors:
                    if v.origin == genetic_source:
                        assert isinstance(v.destination, BanditAgent)

                for agent in agents:
                    assert len(agent.vectors(direction="incoming")) == 1
                    if agent.generation == exp.generations-1:
                        assert len(agent.vectors(direction="all")) == 1

            print("Testing vectors...                   done!")
            sys.stdout.flush()

            """
            TEST INFOS
            """

            print("Testing infos...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=Agent)
                bandits = network.nodes(type=Bandit)
                genetic_source = network.nodes(type=GeneticSource)[0]

                assert len(genetic_source.infos()) == 2
                assert len(genetic_source.infos(type=Gene)) == 2
                assert len(genetic_source.infos(type=MemoryGene)) == 1
                assert len(genetic_source.infos(type=CuriosityGene)) == 1

                for bandit in bandits:
                    assert len(bandit.infos()) == 0

                for agent in agents:
                    infos = agent.infos()
                    assert (len([i for i in infos if isinstance(i, Gene)])) == 2
                    assert (len([i for i in infos if isinstance(i, MemoryGene)])) == 1
                    assert (len([i for i in infos if isinstance(i, CuriosityGene)])) == 1
                    assert (len([i for i in infos if isinstance(i, Pull)])) == len(infos) - 2

                    curiosity = int([i for i in infos if isinstance(i, CuriosityGene)][0].contents)

                    pulls = [i for i in infos if isinstance(i, Pull)]

                    for pull in pulls:
                        if pull.check == "true":
                            assert len([pp for pp in pulls if pp.trial == pull.trial and pp.check == "false"]) == 1
                        else:
                            if pull.remembered == "true":
                                assert len([pp for pp in pulls if pp.trial == pull.trial and pp.check == "true"]) == 0
                            else:
                                assert len([pp for pp in pulls if pp.trial == pull.trial and pp.check == "true"]) == curiosity

                    received_infos = agent.received_infos()
                    assert len(received_infos) == 2

            print("Testing infos...                     done!")
            sys.stdout.flush()

            """
            TEST TRANSMISSIONS
            """

            print("Testing transmissions...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=Agent)
                genetic_source = network.nodes(type=GeneticSource)[0]
                infos = network.infos()

                assert len(genetic_source.transmissions(direction="all", status="pending")) == 0
                assert len(genetic_source.transmissions(direction="incoming", status="all")) == 0
                assert len(genetic_source.transmissions(direction="outgoing", status="received")) == 2*exp.generation_size

                for agent in agents:
                    assert len(agent.transmissions(direction="all", status="pending")) == 0
                    assert len(agent.transmissions(direction="incoming", status="received")) == 2
                    assert len(agent.transmissions(direction="outgoing", status="received")) % 2 == 0

                    if agent.generation == exp.generations-1:
                        assert len(agent.transmissions(direction="outgoing", status="received")) == 0

            print("Testing transmissions...             done!")

            """
            TEST TRANSFORMATIONS
            """

            print("Testing transformations...", end="\r")
            sys.stdout.flush()

            for network in exp.networks():

                agents = network.nodes(type=Agent)
                genetic_source = network.nodes(type=GeneticSource)[0]
                infos = network.infos()

                assert len(genetic_source.transformations()) == 0

                for agent in agents:
                    ts = agent.transformations()
                    assert len(ts) == 2
                    for t in ts:
                        assert isinstance(t, Mutation)

            print("Testing transformations...           done!")

            """
            TEST FITNESS
            """

            print("Testing fitness...", end="\r")
            sys.stdout.flush()

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
