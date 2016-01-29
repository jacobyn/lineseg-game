var tiles_checked = 0;
var decided = false;
var trials_per_network;
var trial_in_this_network = 0;
var round_number = 0;
var number_of_rounds;

// get all the details to correctly present the trial number bar
get_num_trials = function() {
    reqwest({
        url: "/num_trials",
        method: 'get',
        success: function (resp) {
            trials_per_network = resp.n_trials;
            number_of_rounds = resp.practice_repeats + resp.experiment_repeats;
            prepare_trial_info_text();
        }
    });
};

// make a new node
create_agent = function() {
    reqwest({
        url: "/node/" + uniqueId,
        method: 'post',
        type: 'json',
        success: function (resp) {
            round_number = round_number + 1;
            trial_in_this_network = 0;
            my_node_id = resp.node.id;
            my_network_id = resp.node.network_id;
            get_genes();
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

// what is my memory and curiosity?
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
            for (i = 0; i < infos.length; i++) {
                info = infos[i];
                if (info.type == "curiosity_gene") {
                    my_curiosity = info.contents;
                } else {
                    my_memory = info.contents;
                }
            }
            get_num_bandits();
        }
    });
};

// how many bandits are there?
get_num_bandits = function() {
    reqwest({
        url: "/num_bandits",
        method: 'get',
        type: 'json',
        success: function (resp) {
            num_bandits = resp.num_bandits;
            pick_a_bandit();
        }
    });
};

// pick my current bandit
pick_a_bandit = function () {
    current_bandit = Math.floor(Math.random()*num_bandits);
    get_num_tiles();
};

// how many arms does my bandit have?
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

// which is the good arm?
get_treasure_tile = function() {
    reqwest({
        url: "/treasure_tile/" + my_network_id + "/" + current_bandit,
        method: 'get',
        type: 'json',
        success: function (resp) {
            current_treasure_tile = resp.treasure_tile;
            prepare_for_trial();
        }
    });
};

// show the tiles
prepare_for_trial = function() {
    trial_in_this_network = trial_in_this_network + 1;
    prepare_trial_info_text();

    tiles_checked = 0;
    for (i = 0; i < num_tiles; i++) {
        name_of_tile = "#tile_" + (i+1);
        name_of_image = '<img src="/static/images/tile_' + (i+1) + '.png" onClick="check_tile(' + (i+1) + ')"/>';
        $(name_of_tile).html(name_of_image);
        $("#mini_title").html("<p>you are at bandit " + current_bandit + "</p>");
        $("#instructions").html("<p>You can check under " + my_curiosity + " tiles</p>");
    }
};

prepare_trial_info_text = function() {
    $("#trial_number").html(trial_in_this_network);
    $("#number_of_trials").html(trials_per_network);
    $("#round_number").html(round_number);
    $("#number_of_rounds").html(number_of_rounds);
};

// look under a tile
check_tile = function (tile) {
    if (tiles_checked < my_curiosity) {
        reqwest({
            url: "/info/" + my_node_id,
            method: 'post',
            type: 'json',
            data: {
                contents: tile,
                info_type: "Pull",
                property1: true, // check
                property2: current_bandit, // bandit_id
                property3: true // remembered
            },
        });
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
            $("#instructions").html("<p>Please wait...");
            setTimeout(function() {
                prepare_for_decision();
            }, 2000);
        }
    }
};

// prepare the tiles for the final decision
prepare_for_decision = function () {
    decided = false;
    $("#instructions").html("<p>Please make your final choice of tile.</p>");
    for (i = 0; i < num_tiles; i++) {
        name_of_tile = "#tile_" + (i+1);
        name_of_image = '<img src="/static/images/tile_' + (i+1) + '.png" onClick="choose_tile(' + (i+1) + ')"/>';
        $(name_of_tile).html(name_of_image);
    }
};

// commit to a particular tile 
choose_tile = function (tile) {
    if (decided === false) {
        decided = true;
        $("#instructions").html("<p>Your decision is being saved, please wait...</p>");
        reqwest({
            url: "/info/" + my_node_id,
            method: 'post',
            type: 'json',
            data: {
                contents: tile,
                info_type: "Pull",
                property1: false, // check
                property2: current_bandit, // bandit_id
                property3: true // remembered
            },
        });
        name_of_tile = "#tile_" + tile;
        name_of_image = '<img src="/static/images/dot.png"/>';
        $(name_of_tile).html(name_of_image);
        setTimeout(function() {
            advance_to_next_trial();
        }, 2000);
    }
};

advance_to_next_trial = function () {
    if (trial_in_this_network == trials_per_network) {
        reqwest({
            url: "/node/" + my_node_id + "/calculate_fitness",
            method: "get",
            type: 'json',
            error: function (err) {
                console.log(err);
                err_response = JSON.parse(err.response);
                $('body').html(err_response.html);
            }
        });
        create_agent();
    } else {
        pick_a_bandit();
    }
};