
@extra_routes.route("/dashboard/<int:number_of_participants_to_check>/<int:number_of_current_participants>", methods=["GET"])
def dashboard(number_of_participants_to_check,number_of_current_participants):
    try:
        exp = LineGame(db.session)

        #print ("Print contents of {} last particiapnts...".format(number_of_participants_to_check))
        networks = exp.networks()
        # my_part_id=None
        # for network in networks:
        #     agents=network.nodes(type=LineAgent)
        #     for agent in agents:
        #         my_part_id = agent.participant_id
        #         if not(my_part_id==None):
        #             break

        # participants = Participant.query.filter_by(uniqueid=my_part_id).all()
        # print(participants)
        # print('myhitid:' + my_part_id)
        # my_hit_id=participants[0].hitid
        # print('myhitid:' + my_hit_id)


        participants = Participant.query.all()
        # print("*****>>>>")
        # print(participants)

        dates={p.beginhit:p for p in participants}
        sorted_dates_tuples=sorted(dates.items())

        # check that number_of_participants_to_check
        if number_of_participants_to_check==0:
            number_of_participants_to_check= len(sorted_dates_tuples)
        my_num_parts= min ([number_of_participants_to_check, len(sorted_dates_tuples)])

        selected_participants_ids=[k[1].uniqueid for k in sorted_dates_tuples[(-my_num_parts):]]
        current_participants_ids=[k[1].uniqueid for k in sorted_dates_tuples[(-number_of_current_participants):]]
        #print("selected part ids")
        #print(selected_participants_ids)
        #nodes(self, type=None, failed=False, participant_id=None):

#         print("Testing infos...", end="\r")
#            sys.stdout.flush()
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
            summary_node_dict[network.id]['x']=[]
            summary_node_dict[network.id]['y']=[]

            print('summary_node_dict at initialization')
            print (summary_node_dict)
            #source = network.nodes(type=LineSource)[0]
            #print("relevant network")
            #print(network)
            for agent in agents:
                agent_p_id=agent.participant_id
                if agent_p_id in current_participants_ids:
                    summary_node_dict[network.id]['label']=str(network.id) + "|" + str(agent_p_id)
                    summary_node_dict[network.id]['current']=True

                summary_node_dict_fail[agent_p_id]['label']=str(agent_p_id)
                summary_node_dict_fail[agent_p_id]['role']=network.role
                summary_node_dict_fail[agent_p_id]['current']=False
                summary_node_dict_fail[agent_p_id]['x']=[]
                summary_node_dict_fail[agent_p_id]['y']=[]
                print('summary_node_dict_fail at initialization')
                print (summary_node_dict_fail)


                if agent_p_id in current_participants_ids:
                    summary_node_dict_fail[agent_p_id]['label']=str(agent_p_id)+ "<" + str(network.id)
                    summary_node_dict_fail[agent_p_id]['current']=True

                #print("-->relevant agent")
                #print(agent)
                infos =  agent.infos()
                #print("---->>relevant infos")
                #print(infos)
                #print(LineInfo.query.filter_by(origin_id=agent.id).all())
                for info in infos:
                    #print("---->>>>relevant info")
                    #print(info)
                    #print(">>>>>>>>info true seed:")
                    #print(info.true_seed)

                    try:
                        generation=int(info.generation)
                        true_seed=info.true_seed

                        try:
                            contents=int(info.contents)
                            is_fail=info.failed
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
                    if is_fail:
                        gen=1.0*(max([generation-1,0]))+0.8*random.random()
                        summary_node_dict_fail[agent_p_id]['x'].append(gen)
                        summary_node_dict_fail[agent_p_id]['y'].append(true_seed)
                    else:
                        gen=1.0*(generation)+0.8*random.random()
                        summary_node_dict[network.id]['x'][generation]=gen
                        summary_node_dict[network.id]['y'][generation]=target

                        if generation==1:
                           gen=1.0*(0)+0.8*random.random()
                           summary_node_dict[network.id]['x'][0]=gen
                           summary_node_dict[network.id]['y'][0]=value_source



        # chain_lengths = [n.size(type=LineAgent) for n in exp.networks()]
        chain_dic = dict([(n.id,n.size(type=LineAgent)) for n in networks])
        chain_list= [ chain_dic[k] for k in chain_dic.keys()]

        chain_dic_failed = dict([(n.id,n.size(type=None, failed=True)) for n in networks])
        chain_list_failed= [ chain_dic_failed[k] for k in chain_dic_failed.keys()]


        selected_participants_bonus=sum([k[1].bonus for k in sorted_dates_tuples[(-my_num_parts):]])
        all_participants_bonus=sum([k[1].bonus for k in sorted_dates_tuples])

        all_chain_length=sum(chain_list)
        min_chain_length=min(chain_list)
        max_chain_length=max(chain_list)
        num_failed_nodes=len(Node.query.filter_by(failed=True).all())
        selected_participants_num=len(selected_participants_ids)

        str_general_summary="all_bonus={} selected_part_num={} part_bonus={} all_chain_length={} max_chain_length={} min_chain_length={} num_failed_nodes={}".format(all_participants_bonus, selected_participants_num, selected_participants_bonus, all_chain_length, max_chain_length, min_chain_length, num_failed_nodes)
        summary={"all_bonus": all_participants_bonus, "selected_part_num": selected_participants_num, "selected_part_bonus": selected_participants_bonus, "all_chain_length": all_chain_length, "max_chain_length":max_chain_length, "min_chain_length": min_chain_length, "num_failed_nodes": num_failed_nodes, "all_chain_lengths": str(chain_list), "all_chain_lengths_failed": str(chain_list_failed), "summary_node_list":summary_node_list}
        #print(str_general_summary)
        #print(summary)
        return Response(
                dumps(summary),
                status=200,
                mimetype='application/json')

#        return Response(dumps(summary), status=200)
    except Exception:
        import traceback
        return Response(dumps(traceback.print_exc()), status=400)
