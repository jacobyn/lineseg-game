var trial = 0;
var num_trials;
var num_practice_trials;
var tiles_checked = 0;

get_num_trials = function() {
    reqwest({
        url: "/num_trials",
        method: 'get',
        success: function (resp) {
            num_trials = (resp.practice_repeats + resp.experiment_repeats)*resp.n_trials;
            num_practice_trials = resp.practice_repeats*resp.n_trials;
            $("#num_trials").html(num_trials);
            if (trial <= num_practice_trials) {
                $("#practice-trial").html("This is a practice trial");
            } else {
                $("#practice-trial").html("This is NOT a practice trial");
            }
        }
    });
};

// make a new node
create_agent = function() {
    trial = trial + 1;
    $("#trial-number").html(trial);
    if (trial <= num_practice_trials) {
        $("#practice-trial").html("This is a practice trial");
    } else {
        $("#practice-trial").html("This is NOT a practice trial");
    }

    reqwest({
        url: "/node/" + uniqueId,
        method: 'post',
        type: 'json',
        success: function (resp) {
            my_node_id = resp.node.id;
            my_network_id = resp.node.network_id;
            get_num_bandits();
        },
        error: function (err) {
            console.log(err);
            err_response = JSON.parse(err.response);
            if (err_response.hasOwnProperty('html')) {
                $('body').html(err_response.html);
            } else {
                allow_exit();
                window.location = "/debrief/1?hit_id=" + hit_id + "&assignment_id=" + assignment_id + "&worker_id=" + worker_id + "&mode=" + mode;
            }
        }
    });
};

get_num_bandits = function() {
    reqwest({
        url: "/num_bandits",
        method: 'get',
        type: 'json',
        success: function (resp) {
            num_bandits = resp.num_bandits;
            current_bandit = Math.floor(Math.random()*num_bandits);
            get_num_tiles();
        }
    });
};

get_num_tiles = function() {
    reqwest({
        url: "/num_arms/" + my_network_id + "/" + current_bandit,
        method: 'get',
        type: 'json',
        success: function (resp) {
            num_tiles = resp.num_tiles;
            get_treasure_tile();
        }
    });
};

get_treasure_tile = function() {
    reqwest({
        url: "/treasure_tile/" + my_network_id + "/" + current_bandit,
        method: 'get',
        type: 'json',
        success: function (resp) {
            current_treasure_tile = resp.treasure_tile;
            get_genes();
        }
    });
};

get_genes = function() {
    reqwest({
        url: "/node/" + my_node_id + "/infos",
        method: 'get',
        type: 'json',
        data: {
            info_type: "Gene"
        },
        success: function (resp) {
            infos = resp.infos;
            console.log(infos);
            for (i = 0; i < infos.length; i++) {
                info = infos[i];
                if (info.type == "curiosity_gene") {
                    my_curiosity = info.contents;
                } else {
                    my_memory = info.contents;
                }
            }
            prepare_for_trial();
        }
    });
};

prepare_for_trial = function() {
    tiles_checked = 0;
    for (i = 0; i < num_tiles; i++) {
        name_of_tile = "#tile_" + (i+1);
        name_of_image = '<img src="/static/images/tile_' + (i+1) + '.png" onClick="check_tile(' + (i+1) + ')"/>';
        $(name_of_tile).html(name_of_image);
        $("#mini_title").html("<p>you are at bandit " + current_bandit + "</p>");
        $("#instructions").html("<p>You can check under " + my_curiosity + " tiles</p>");
    }
};

check_tile = function (tile) {
    if (tiles_checked < my_curiosity) {
        tiles_checked = tiles_checked + 1;
        name_of_tile = "#tile_" + tile;
        if (tile == current_treasure_tile) {
            name_of_image = '<img src="/static/images/treasure.png"/>';
            $(name_of_tile).html(name_of_image);
        } else {
            name_of_image = '<img src="/static/images/no.png"/>';
            $(name_of_tile).html(name_of_image);
        }
        if (tiles_checked == my_curiosity) {
            prepare_for_decision();
        }
    }
};

prepare_for_decision = function () {

};








get_levels = function() {
    reqwest({
        url: "levels/" + my_network_id,
        method: "get",
        success: function (resp) {
            levels = resp.levels;
            if (my_generation > 0) {
                get_summary();
            } else {
                get_seed_summary();
            }
        }
    });
};

get_summary = function() {
    reqwest({
        url: "node/" + my_node_id + "/received_infos",
        method: 'get',
        data: { info_type: "Summary" },
        type: 'json',
        success: function(resp) {
            content = JSON.parse(resp.infos[0].contents);
            num_cooperate_1 = content["num_cooperate_1"];
            num_defect_1 = content["num_defect_1"];
            num_cooperate_2 = content["num_cooperate_2"];
            num_defect_2 = content["num_defect_2"];
            num_cooperate_3 = content["num_cooperate_3"];
            num_defect_3 = content["num_defect_3"];
            payoff_cooperate_1 = content["payoff_cooperate_1"];
            payoff_defect_1 = content["payoff_defect_1"];
            payoff_cooperate_2 = content["payoff_cooperate_2"];
            payoff_defect_2 = content["payoff_defect_2"];
            payoff_cooperate_3 = content["payoff_cooperate_3"];
            payoff_defect_3 = content["payoff_defect_3"];
            draw_level();
        }
    });
};

get_seed_summary = function() {
    num_cooperate_1 = 5;
    num_defect_1 = 5;
    num_cooperate_2 = 5;
    num_defect_2 = 5;
    num_cooperate_3 = 5;
    num_defect_3 = 5;
    payoff_cooperate_1 = 5;
    payoff_defect_1 = 5;
    payoff_cooperate_2 = 5;
    payoff_defect_2 = 5;
    payoff_cooperate_3 = 5;
    payoff_defect_3 = 5;
    draw_level();
};

draw_level = function() {
    if (level === 0) {
        $("#instruction_question_1").html("You are starting a new round");
        $("#instruction_details_1").html("");
        $("#instruction_qualifier_1").html("");
        $("#social_information_1").html("");
        $("#social_information2_1").html("");
        $("#instruction_keys_1").html("Click the button below to begin.");
        $("#radio_buttons_1").html("");
        $("#instruction_question_2").html("");
        $("#instruction_details_2").html("");
        $("#instruction_qualifier_2").html("");
        $("#social_information_2").html("");
        $("#social_information2_2").html("");
        $("#instruction_keys_2").html("");
        $("#radio_buttons_2").html("");
        $("#instruction_question_3").html("");
        $("#instruction_details_3").html("");
        $("#instruction_qualifier_3").html("");
        $("#social_information_3").html("");
        $("#social_information2_3").html("");
        $("#instruction_keys_3").html("");
        $("#radio_buttons_3").html("");
        $("#begin_button").show();
        $("#submit_button").hide();
        $("#radio_div_1").hide();
        $("#radio_div_2").hide();
        $("#radio_div_3").hide();
        $("#null_1").prop("checked", true);
        $("#null_2").prop("checked", true);
        $("#null_3").prop("checked", true);
        start_lock = false;
    } else {
        $("#begin_button").hide();
        $("#submit_button").show();
        $("#radio_div_1").show();
        $("#instruction_question_1").html("Do you want to contribute to the investment fund?");
        $("#instruction_details_1").html("Doing so will cost you 10 points. The total investment from all players is doubled and then shared equally among everyone.");
        if (levels == 1) {
            $("#instruction_qualifier_1").html("Accountants are not available for hire in this round, so you cannot be fined for not contributing.");
        } else {
            $("#instruction_qualifier_1").html("Accountants are available for hire in this round, so if you do not contribute you may be fined by other players.");
        }
        if (payoff_cooperate_1 > 0) {
            $("#social_information_1").html("In the previous group, <b>" + num_cooperate_1 + "</b> members contributed, on average gaining <b>" + payoff_cooperate_1 + "</b> points.");
        } else {
            $("#social_information_1").html("In the previous group, <b>" + num_cooperate_1 + "</b> members contributed, on average losing <b>" + payoff_cooperate_1 + "</b> points.");
        }
        if (payoff_defect_1 > 0) {
            $("#social_information2_1").html("However, <b>" + num_defect_1 + "</b> members did not contribute, on average gaining <b>" + payoff_defect_1 + "</b> points.");
        } else {
            $("#social_information2_1").html("However, <b>" + num_defect_1 + "</b> members did not contribute, on average losing <b>" + payoff_defect_1 + "</b> points.");
        }
        $("#instruction_keys_1").html("Please use the radio buttons below to make your choice.");
        if (levels > 1) {
            $("#radio_div_2").show();
            $("#instruction_question_2").html("Do you want to hire an accountant?");
            $("#instruction_details_2").html("They will fine members who did not contribute to the fund 5 points each, but will cost you 1 point for every member they fine.");
            if (levels == 2) {
                $("#instruction_qualifier_2").html("Investigators are not available for hire in this round so you cannot be fined for not hiring an accountant.");
            } else {
                $("#instruction_qualifier_2").html("Investigators are available for hire in this round, so if you do not hire an accountant you may be fined by other players.");
            }
            $("#social_information_2").html("In the previous group, <b>" + num_cooperate_2 + "</b> members hired an accountant, on average spending <b>" + payoff_cooperate_2 + "</b> points.");
            if (levels == 2) {
                $("#social_information2_2").html("However, <b>" + num_defect_2 + "</b> members did not hire an accountant.");
            } else {
                $("#social_information2_2").html("However, <b>" + num_defect_2 + "</b> members did not hire an accountant, on average being fined <b>" + payoff_defect_2 + "</b> points.");
            }
            $("#instruction_keys_2").html("Please use the radio buttons below to make your choice.");
            if (levels > 2) {
                $("#radio_div_3").show();
                $("#instruction_question_3").html("Do you want to hire an investigator?");
                $("#instruction_details_3").html("They will fine members who did not hire an accountant 5 points each, but will cost you 1 point for every member they fine.");
                $("#instruction_qualifier_3").html("You cannot be fined, or fine others, for not hiring an investigator.");
                $("#social_information_3").html("In the previous group, <b>" + num_cooperate_3 + "</b> members hired an investigator, on average spending <b>" + payoff_cooperate_3 + "</b> points.");
                $("#social_information2_3").html("However, <b>" + num_defect_3 + "</b> members did not hire an investigator.");
                $("#instruction_keys_3").html("Please use the radio buttons below to make your choice.");
            }
        }
    }
};

draw_question = function() {
    level = level + 1;
    draw_level();
};

submit_answers = function() {
    complete = true;
    level_1_answer = $("input[name=invest]:checked").val();
    if (level_1_answer == "-1") {
        $("#warning_1").html("Please choose whether or not to contribute to the investment fund.");
        complete = false;
    } else {
        $("#warning_1").html("");
    }
    if (levels > 1) {
        level_2_answer = $("input[name=secretary]:checked").val();
        if (level_2_answer == "-1") {
            $("#warning_2").html("Please choose whether or not to hire a secretary.");
            complete = false;
        } else {
            $("#warning_2").html("");
            complete = true;
        }
    }
    if (levels > 2) {
        level_3_answer = $("input[name=accountant]:checked").val();
        if (level_3_answer == "-1") {
            $("#warning_3").html("Please choose whether or not to hire an accountant.");
            complete = false;
        } else {
            $("#warning_3").html("");
            complete = true;
        }
    }
     if (complete === true) {
        reqwest({
            url: "/info/" + my_node_id + '/' + 1,
            method: 'post',
            type: 'json',
            data: {
                contents: level_1_answer,
                info_type: "Decision"
            },
            success: function(resp) {
                if (levels > 1) {
                    reqwest({
                        url: "/info/" + my_node_id + '/' + 2,
                        method: 'post',
                        type: 'json',
                        data: {
                            contents: level_2_answer,
                            info_type: "Decision"
                        },
                        success: function(resp) {
                            if (levels > 2) {
                                reqwest({
                                    url: "/info/" + my_node_id + '/' + 3,
                                    method: 'post',
                                    type: 'json',
                                    data: {
                                        contents: level_3_answer,
                                        info_type: "Decision"
                                    },
                                    success: function(resp) {
                                        create_agent();
                                    },
                                    error: function (err) {
                                        console.log(err);
                                        err_response = JSON.parse(err.response);
                                        $('body').html(err_response.html);
                                    }
                                });
                            } else {
                                create_agent();
                            }
                        },
                        error: function (err) {
                            console.log(err);
                            err_response = JSON.parse(err.response);
                            $('body').html(err_response.html);
                        }
                    });
                } else {
                    create_agent();
                }
            },
            error: function (err) {
                console.log(err);
                err_response = JSON.parse(err.response);
                $('body').html(err_response.html);
            }
        });
    }
};
