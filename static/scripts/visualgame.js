//var norm_dist_x = undefined;
//var norm_dist_y = undefined;


////////////////////////////////////// NORI ///////////////////

var DO_WALLACE = false;
var WAIT_TIME = 2000; // in between trials wait time
var MAX_TIME_TRIAL = 20 * 1000;

 // set to correct or incorrect
var outcome = undefined;
var DEBUG = true;
var my_node_id;
var my_network_id;
var generation;
var mytrial_params = 'EMPTY';
var mycontents = 'EMPTY';
var myresponse = 'EMPTY';
var myrt = 0;
var err_time = undefined;

function create_agent() {
    outcome = undefined;
    my_node_id = undefined;
    my_network_id = undefined
    generation = undefined
    mytrial_params = 'EMPTY';
    mycontents = 'EMPTY';
    myresponse = 'EMPTY';
    myrt = 0;
    err_time = undefined;

    if (DEBUG) {
        console.log ("(1) create agent" )
    }
    err_time = setTimeout(function(){},MAX_TIME_TRIAL); // just set time don't do anything actually

    reqwest({
        url: "/node/" + participant_id,
        method: 'post',
        type: 'json',
        success: function (resp) {

            my_node_id = resp.node.id;
             if (DEBUG) {
               console.log("-->(2) create agent: node id:  " + my_node_id + "__ participant_id:  " + participant_id);
            }
            my_network_id = resp.node.network_id;
            get_trial_params()

        },
        error: function (err) {
            console.log(err);
            err_response = JSON.parse(err.response);
            if (err_response.hasOwnProperty('html')) {
                $('body').html(err_response.html);
            } else {
                //$('body').html(err_response)
                allow_exit();
                go_to_page("debriefing/debrief-1");
            }
        }
    });
};

function get_trial_params() {
    if (DEBUG) {
        console.log("(3) trial: get_trial_params"  );
    }
   reqwest ({
    // /get_trial_params/<int:node_id>/<int:participant_id>", methods=["GET"])
    url: "/get_trial_params/" + my_network_id +"/"+ participant_id     ,
    method: 'get',
    type: 'json',
    success: function (resp) {
        if (DEBUG) {
               console.log("--->(4) get trial params:" );
               console.log(resp);
            }

        mytrial_params=resp.trial_params
        generation = resp.generation;

        get_contents(mytrial_params);
      },
      error: function (err) {

        console.log(err);
        clearTimeout(err_time);
        err_time = setTimeout(function(){create_agent();},WAIT_TIME*2);
    }
});
}

function get_contents(mytrial_params) {
    if (DEBUG) {
        console.log("(5) get_contents" );
    }
    reqwest ({
        url: "/node/" + my_node_id + "/received_infos",
        method: 'get',
        type: 'json',
        success: function (resp) {
            if (DEBUG) {
               console.log("---> (6) we received_infos");
                console.log(resp);

            }
            mycontents=resp.infos[0].contents

            get_params(mycontents,mytrial_params);
            set_src();
            init();
        },
        error: function (err) {
        console.log(err);
        clearTimeout(err_time);
        err_time = setTimeout(function(){create_agent();},WAIT_TIME*2);
        }
    });
}

// draw things on the screen
function init() {
    if (DEBUG) {
        console.log ("(6) Init!" );
    }
     // call get_params


    // init the target image position
    var trial_image = document.getElementById('trial_image'); // .x and .y give x and y offsets from the edge of the page (screen)
    var trial_bcgrd = document.getElementById('trial_bcgrd'); // .x and .y
    // normalized position of image in timed presentation relative
    // to top left corner of position of bcgrd during presentation

    // Set position using normalized offset values (which we will get from Wallace)
    var cont = function() {
      setImagePosition(trial_image, trial_bcgrd, x_Correct, y_Correct);
      ShowTrialStart(currentTrial);
      document.getElementById("trial_image").style.visibility = "visible";
    };
    var ti = $('#trial_image');
    if (ti[0].complete) {
      cont();
    } else {
      ti.load(cont);
    }
}

// send result to server
function finished(){
    if (DEBUG) {
        console.log ("(f) Finished" );

    }

   reqwest({
    url: "/info/" + my_node_id,
    method: 'post',
    type: 'json',
    data: {
        contents: myresponse,
        info_type: "VisionInfo",
            property1: mycontents, // number of failed trials
            property2: myrt, // bandit_idf
            property3: 0, // remembered
            property4: 0,
            property5: generation
        },
        success: function (resp) {
             if (DEBUG) {
               console.log ("(f) --> finished ok!" );
            }

            setTimeout(function(){create_agent();},WAIT_TIME);
        },
        error: function (err) {
            console.log(err);
            clearTimeout(err_time);

            err_time = setTimeout(function(){create_agent();},WAIT_TIME/2);

        }
  });
}

////////////////////////////////////// THOMAS and NORI///////////////////

function get_params(contents,trial_params) {
    if (DO_WALLACE) {
        // Parse JSON object (named mytrial_params)
        // var trial_params = JSON.parse(mytrial_params);
        // contents (need to parse this, it's a string)
        // var contents = JSON.parse(mycontents);
        mycontents = JSON.parse(contents);
        mytrial_params = JSON.parse(trial_params);
        contents=mycontents;
        trial_params=mytrial_params;

        // get normalized horizontal offset of target (from left border of background)
        x_Correct = contents[0]; // contents[0];
        // get normalized vertical offset of target (from left border of background)
        y_Correct = contents[1]; // contents[1];

        // get image source for target image (e.g. runner)
        target_src = trial_params.target_src; // "https://s3.amazonaws.com/thomas-nori-projects/F2114.png" // trial_params.target_src;
        // get image source for background image (e.g. race track)
        bcgrd_src = trial_params.bcgrd_src;//"https://s3.amazonaws.com/thomas-nori-projects/B2114.jpg"; // trial_params.bcgrd_src;

        // trial number
        // (update the trial number information below next function)

        // timed presentation value (ms)
        pres_time = trial_params.pres_time; //3000; // trial_params.pres_time;

        // timed fixation value (ms)
        fix_time = trial_params.fix_time;//1000; // trial_params.fix_time;

        // Margins of error on x, and y (between 0 and 1)
        margin_error_x = trial_params.margin_error_x;//0.05; // trial_params.margin_error_x;
        margin_error_y = trial_params.margin_error_y;//0.05; // trial_params.margin_error_y;

        // deltas for locations of timed presentations (to avoid cheating)
        // one of four positions? top, bottom, left, right
        delta_x = trial_params.delta_x;///0.0;
        delta_y = trial_params.delta_y;//0.0;

    // node: return "none" if incorrect choice
    } else {
         x_Correct = 0.5;
        // get normalized vertical offset of target (from left border of background)
         y_Correct = 0.5;

        // get image source for target image (e.g. runner)
        target_src = "https://s3.amazonaws.com/thomas-nori-projects/F2114.png" // trial_params.target_src;
        // get image source for background image (e.g. race track)
        bcgrd_src = "https://s3.amazonaws.com/thomas-nori-projects/B2114.jpg"; // trial_params.bcgrd_src;

        // trial number
        // (update the trial number information below next function)

        // timed presentation value (ms)
        pres_time = 3000; // trial_params.pres_time;

        // timed fixation value (ms)
        fix_time = 1000; // trial_params.fix_time;

        // Margins of error on x, and y (between 0 and 1)
        margin_error_x = 0.05; // trial_params.margin_error_x;
        margin_error_y = 0.05; // trial_params.margin_error_y;

        // deltas for locations of timed presentations (to avoid cheating)
        // one of four positions? top, bottom, left, right
        delta_x = 0.0;
        delta_y = 0.0;
    }

}

function make_response(chosen_x, chosen_y, rt) {
    // if trial was incorrect return a string like this: "NaN"
    // if correct return String([chosen_x, chosen_y])
    if (outcome === "Correct") {
        myresponse = String([chosen_x, chosen_y])
    } else if (outcome === "Incorrect") {
        myresponse = "NaN";
    }
    myrt=rt;
    if (DO_WALLACE) {finished();}

}

$(document).ready(function(){
    console.log("ready!");
    if (DO_WALLACE) { create_agent ();} else  {init()}

    // // call get_params
    // get_params()
    // set_src()

    // // init the target image position
    // var trial_image = document.getElementById('trial_image'); // .x and .y give x and y offsets from the edge of the page (screen)
    // var trial_bcgrd = document.getElementById('trial_bcgrd'); // .x and .y
    // // normalized position of image in timed presentation relative
    // // to top left corner of position of bcgrd during presentation

    // // Set position using normalized offset values (which we will get from Wallace)
    // var cont = function() {
    //   setImagePosition(trial_image, trial_bcgrd, x_Correct, y_Correct);
    //   ShowTrial(currentTrial);
    // };
    // var ti = $('#trial_image');
    // if (ti[0].complete) {
    //   cont();
    // } else {
    //   ti.load(cont);
    // }
});

////////////////////////////////////// THOMAS ///////////////////

function checkS(e){
// capture the mouse position
    var posx = 0;
    var posy = 0;
    if (!e) var e = window.event;
    if (e.pageX || e.pageY)
    {
        posx = e.pageX;
        posy = e.pageY;
    }
    else if (e.clientX || e.clientY)
    {
        posx = e.clientX; //  relative to the top left corner of the webpage. clientX is what I want
        posy = e.clientY; //  e.target.x  //  e.screenX   //   clientX  just do: ( e.target.x - e.clientX ) /
    }
    // make dot visible as soon as it is placed somewhere
    document.getElementById("image").style.visibility = "visible";
    // document.getElementById('image').style.position = 'absolute';

    var myImg = document.querySelector("#image");
    var realWidth = myImg.naturalWidth;
    var realHeight = myImg.naturalHeight;

    document.getElementById('image').style.left = posx - realWidth * 0.5 + 'px';
    document.getElementById('image').style.top = posy - realHeight * 0.5 + 'px';

    chosenx = posx;
    choseny = posy;

    // normalized distance of the target image to the top left corner of the background
    // this is still not quite right
    norm_dist_x = ( e.clientX - e.target.x ) / e.target.width;  //try pageX, but might need to change target.width (problem with zooming)
    norm_dist_y = ( e.clientY - e.target.y ) / e.target.height; //try pageY, but might need to change target.height (problem with zooming)
}

// Trial functions (next trial etc)
var order = new Array(11,12);
var currentTrial = 0; // changed from 1 to 0!

function setImagePosition(image, background, normX, normY) {
    image.style.left =
      (normX * background.width + background.x - (image.width / 2)) + 'px';
    image.style.top =
      (normY * background.height + background.y - (image.height / 2)) + 'px';
}

// JSON object? or string?

// trial params
// vs
// global parameters



function set_src() {
    // set image src for presentation, trial, and feedback pages
    // Target image
    document.getElementById("trial_image").src = target_src;
    document.getElementById("image").src = target_src;
    document.getElementById("image_feedback").src = target_src;
    // Background image
    document.getElementById("trial_bcgrd").src = bcgrd_src;
    document.getElementById("bcgrd").src = bcgrd_src;
    document.getElementById("bcgrd_feedback").src = bcgrd_src;
}

function ShowTrialStart(which) {
        // init the target somewhere on the canvas (center)
        var myImg = document.querySelector("#trial_bcgrd");
        var Width_bcgrd = myImg.naturalWidth;
        var Height_bcgrd = myImg.naturalHeight;
        // init hidden image at center of background
        document.getElementById('image').style.position = 'absolute';
        document.getElementById('image').style.left = Width_bcgrd * 0.5 + 'px';
        document.getElementById('image').style.top = Height_bcgrd * 0.5 + 'px';

        // show trial page
        var page = "#page" + order[which];
        var pageTimed = "#trial";
        var fixation = "#fix";

        $(pageTimed).show();
        setTimeout(function() {
            $(pageTimed).hide();
            $(".fix").css('visibility', 'visible');
            $(fixation).show()
            setTimeout(function() {
                $(".fix").css('visibility', 'hidden');
                $(fixation).hide();
                // show drag-drop trial
                $(page).show();
            }, fix_time);
        }, pres_time);

        // $(page).show();
        var showTrial = which+1; // 0 indexed to 1 indexed
        $(".currentTrialIndicator").text("Current trial: " + showTrial + " of " + order.length); // replace trial number
}


function ShowTrialEnd(which) {
        var page = "#page" + order[which];
        $(page).show();

        // present image in the position chosen for feedback page
        var feedbackImage = document.getElementById('image_feedback');
        var feedbackBackground = document.getElementById('bcgrd_feedback');
        setImagePosition(feedbackImage, feedbackBackground, norm_dist_x, norm_dist_y);


        rt = 0; // <get response time...>
        make_response(norm_dist_x, norm_dist_y, rt);

        // for changing the feedback message
        var fieldNameElement = document.getElementById('field_name');

        if (Math.abs(norm_dist_x - x_Correct) < margin_error_x
               && Math.abs(norm_dist_y - y_Correct) < margin_error_y) {
            // make border green if correct
            feedbackBackground.style.borderColor = '#00FF00'; //#ff8080
            // Display feedback message (correct!)
            fieldNameElement.innerHTML = "You are correct!";
            outcome = "Correct"
        } else {
            // make border red if incorrect
            feedbackBackground.style.borderColor= '#ff8080';
            // display feedback message (incorrect!)
            fieldNameElement.innerHTML = "You are not correct";
            outcome = "Incorrect"
        }

}

function NextTrial() {
    var checkedValue = $("input[type=radio]:checked"); //adapt this. No radio buttons here
    if (currentTrial === 0) { //&& checkedValue.length === 0) {
    //     alert('You must move the object');
    // } else {
        $("#page" + order[currentTrial]).hide();
        currentTrial++;
        setTimeout(function() {
            ShowTrialEnd(currentTrial);
        }, 1000);
    }
}
