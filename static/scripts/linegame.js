var SQ_X=20;   // begining of square
var SQ_Y=20;   // begining of square
var SQ_W=600;  // width of square
var SQ_H=100;  // height of square
var SQ_R=3;    // roundness of square (aethtetics)
var PROX_T=11; // the threshold what is an error in the command-line
var err_time=undefined;
// RANGE LINEGAME
//var RANGE_MIN=0
//var RANGE_MAX=100

//var RANGE_MIN=15
//var RANGE_MAX=85 // this was run 12 apr morning

var RANGE_MIN=12 // we cahnge it to imitate the UI, that allow some slack from both sides
var RANGE_MAX=88

// inputs:
var TRUE_RATIO=NaN; // input
var IS_FEEDBACK=false; //give feedback?

var TRIAL_WAIT_TIME=2000; // in between trials wait time
var MAX_TIME_TRIAL=20*1000;
var MAX_REPATS=3;   // maximal number of repetiotions to try find correct response

var DEBUG=true; // plot internal variables (for debug puropose) on console
var DEBUG2=false; // plot internal variables on screen!


// outputs:
var results=[]; //output list
var result;    //the final output (NaN if incorrect)
var repeats=0; //number of repeats
var reactionTime=0;
var timeStarted;
var stage; // global variable holding the stage (canvas)

var do_not_click_again=false;
var timer_max_trial;
var GENERATION=-1;
var MAX_ATTEMPTS=1000;
var current_trial= 0;
var number_of_clicks_in_attempts = new Array(MAX_ATTEMPTS)

for (i=0;i<=MAX_ATTEMPTS;i++) {
   number_of_clicks_in_attempts[i]=0;
}

function print_gen() {
    for (i=0;i<MAX_ATTEMPTS;i++){
        if (number_of_clicks_in_attempts[i]>0) {
            idx=current_trial*MAX_REPATS+Math.min(repeats,MAX_REPATS);
            console.log("     idx=" + idx + " gen: " + (idx/MAX_REPATS) + " clicks: " + number_of_clicks_in_attempts[i]);
        }
    }
}


function create_agent () {
    if (DEBUG) {
        console.log ("(1) trial:" + current_trial + " repeats:" + repeats + " function: " + "create_agent");
    }
    results=[]; //output list
    repeats=0; //number of repeats
    reactionTime=0;
    TRUE_RATIO= RANGE_MIN + Math.floor(Math.random()*(RANGE_MAX-RANGE_MIN + 1));

    timer_max_trial=setTimeout(function(){timeOver()},MAX_TIME_TRIAL);

    reqwest({
        url: "/node/" + participant_id,
        method: 'post',
        type: 'json',
        success: function (resp) {
            if (DEBUG) {
               console.log ("--->(1) trial:" + current_trial + " repeats:" + repeats + " reqwest: " + "node" + + "__ participant_id" + participant_id);
            }

            my_node_id = resp.node.id;
            my_network_id = resp.node.network_id;
            getIsPractice();

        },
        error: function (err) {
            console.log(err);
            err_response = JSON.parse(err.response);
            if (err_response.hasOwnProperty('html')) {
                $('body').html(err_response.html);
            } else {
                allow_exit();
                go_to_page("debriefing/debrief-1");
            }
        }
    });
};

function getIsPractice() {
    if (DEBUG) {
        console.log ("(2) trial:" + current_trial + " repeats:" + repeats + " function: " + "getIsPractice" );
    }
   reqwest ({
    url: "/is_practice/" + my_network_id,
    method: 'get',
    type: 'json',
    success: function (resp) {
        if (DEBUG) {
               console.log ("--->(2) trial:" + current_trial + " repeats:" + repeats + " reqwest: " + "is_practice");
            }

        IS_FEEDBACK = resp.is_practice;
        WAIT_TIME=TRIAL_WAIT_TIME;
            if (IS_FEEDBACK) { // if practice randomize from scratch each time
              TRUE_RATIO=RANGE_MIN + Math.floor(Math.random()*(RANGE_MAX-RANGE_MIN + 1));
              WAIT_TIME=TRIAL_WAIT_TIME+1000;
          }

          startInit();
      },
      error: function (err) {

        console.log(err);
        clearTimeout(err_time);
        err_time=setTimeout(function(){create_agent();},WAIT_TIME*2);
    }
});
}

function getTrialNum() {
    if (DEBUG) {
        console.log ("(5) trial:" + current_trial + " repeats:" + repeats + " function: " + "getTrialNum");
    }
   reqwest ({
    url: "/trial_number_string/" + my_node_id + "/" + participant_id,
    method: 'get',
    type: 'json',
    success: function (resp) {
        if (DEBUG) {
               console.log ("---> (5) trial:" + current_trial + " repeats:" + repeats + " reqwest: " + "trial_number_string");
            }

        TRIAL_STR = resp.trial_str;
        current_trial=parseInt(TRIAL_STR.split("/")[0]);
        GENERATION = resp.generation;
        document.getElementById("Counter").innerHTML=TRIAL_STR;
    },
    error: function (err) {
        console.log(err);
        clearTimeout(err_time);
        err_time=setTimeout(function(){create_agent();},WAIT_TIME*2);
    }
});
}


// get the seed from server:
function startInit() {
    if (DEBUG) {
        console.log ("(3) trial:" + current_trial + " repeats:" + repeats + " function: " + "startInit");
    }

    reqwest ({
        url: "/node/" + my_node_id + "/received_infos",
        method: 'get',
        type: 'json',
        success: function (resp) {
            if (DEBUG) {
               console.log ("---> (3) trial:" + current_trial + " repeats:" + repeats + " reqwest: " + "received_infos");
            }

            TRUE_RATIO=Number(resp.infos[0].contents)
            if (IS_FEEDBACK) { // if practice randomize from scratch each time
              TRUE_RATIO=RANGE_MIN + Math.floor(Math.random()*(RANGE_MAX-RANGE_MIN + 1));
             }

            init();
        },
        error: function (err) {
        console.log(err);
        clearTimeout(err_time);
        err_time=setTimeout(function(){create_agent();},WAIT_TIME*2);
        }
    });
};


// draw things on the screen
function init() {
    if (DEBUG) {
        console.log ("(4) +-> trial:" + current_trial + " repeats:" + repeats + " function: " + "init");
    }
    stage = new createjs.Stage("demoCanvas");

    var square = new createjs.Shape();
    square.graphics.setStrokeStyle(2).beginStroke("black").beginFill("gray").drawRoundRect(SQ_X, SQ_Y, SQ_W, SQ_H,SQ_R,SQ_R,SQ_R,SQ_R);
    stage.addChild(square);
    stage.update();
    timeStarted=performance.now();
    square.addEventListener("click", handleClick);
    document.getElementById("Target").innerHTML= "Target: "+ TRUE_RATIO + " % ";
    document.getElementById("Target").style.color = "green";
    document.getElementById("Feedback").style.color = "black";
    document.getElementById("Feedback").innerHTML="Segment the bar according to the target percentage:"
    currentRepeat=repeats;
    getTrialNum();
    do_not_click_again=false;

}

// send result to server
function finished(){
    if (DEBUG) {
        console.log ("(6) trial:" + current_trial + " repeats:" + repeats + " function: " + "finished");

    }
    if (do_not_click_again) {
        if (DEBUG) {
            console.log("exiting because do not click again");
        }
        return 0;
    };

    do_not_click_again=true;
    clearTimeout(timer_max_trial);

   reqwest({
    url: "/info/" + my_node_id,
    method: 'post',
    type: 'json',
    data: {
        contents: result,
        info_type: "LineInfo",
            property1: repeats, // number of failed trials
            property2: reactionTime, // bandit_id
            property3: TRUE_RATIO, // remembered
            property4: results.toString(),
            property5: GENERATION
        },
        success: function (resp) {
             if (DEBUG) {
               console.log ("(6) --> trial:" + current_trial + " repeats:" + repeats + " reqwest: " + "info");
            }

            setTimeout(function(){create_agent();},WAIT_TIME);
        },
        error: function (err) {
            console.log(err);
            clearTimeout(err_time);

            err_time=setTimeout(function(){create_agent();},WAIT_TIME/2);

        }
  });
}

// cant wait so long... abort and send NaN result
function timeOver() {

    if (DEBUG) {
        console.log ("trial:" + current_trial + " repeats:" + repeats + " function: " + "timeOver");
    }
    //if (current_repeat!=repeats){return;}
    document.getElementById("Feedback").innerHTML= "Time over! You only have " + Math.round(MAX_TIME_TRIAL/1000) + " seconds to complete the trial!";
    document.getElementById("Counter").innerHTML="You may lose bonus.";
    document.getElementById("Feedback").style.color = "red";
    result="NaN";
    //results.push(result);


    reactionTime=Math.round((performance.now()-timeStarted)*10)/10;
    var square = new createjs.Shape();
    square.graphics.setStrokeStyle(5).beginStroke("red").beginFill("gray").drawRoundRect(SQ_X, SQ_Y, SQ_W, SQ_H,SQ_R,SQ_R,SQ_R,SQ_R);
    stage.addChild(square);
    stage.update();
    do_not_click_again=false;
    finished();
}

  // Click happenened: manage interface
  function handleClick(event){

    if (DEBUG) {
        console.log ("(5) trial:" + current_trial + " repeats:" + repeats + " function: " + "handleClick");
    }

    if ((GENERATION>=0) && (repeats>0))  {
        idx=current_trial*MAX_REPATS+Math.min(repeats,MAX_REPATS);
        number_of_clicks_in_attempts[idx]=number_of_clicks_in_attempts[idx]+1;
        if (number_of_clicks_in_attempts[idx]>1) {
            if (DEBUG) {
                console.log ("exiting because: idx=" + idx + "number_of_clicks_in_attempts[idx]" + number_of_clicks_in_attempts[idx] );
            }
            return 0;
        }
    }

    reactionTime=Math.round((performance.now()-timeStarted)*10)/10;

    res_x= event.stageX;
    res_xr=Math.round(100*(res_x-SQ_X)/SQ_W);
    true_xr=TRUE_RATIO;
    true_x=SQ_X+SQ_W*Math.round(true_xr)/100;
    var isCorrect=false;
    results.push(res_xr);

    if  ( (Math.abs(res_xr-true_xr)<PROX_T) && ((res_xr>=RANGE_MIN) && (res_xr<=RANGE_MAX)) ) {
        isCorrect=true;
        result=res_xr;
    } else {
        result="NaN";
    }
    repeats=repeats+1;


	var square = new createjs.Shape(); // this will paint over original square also will not allow furhter clicking (hide square)
	if (isCorrect) {
        square.graphics.setStrokeStyle(3).beginStroke("green").beginFill("gray").drawRoundRect(SQ_X, SQ_Y, SQ_W, SQ_H,SQ_R,SQ_R,SQ_R,SQ_R);
    }
    else {
        square.graphics.setStrokeStyle(5).beginStroke("red").beginFill("gray").drawRoundRect(SQ_X, SQ_Y, SQ_W, SQ_H,SQ_R,SQ_R,SQ_R,SQ_R);
    }

    var res_square = new createjs.Shape();
    res_square.graphics.beginStroke("white").beginFill("white").drawRect(res_x, SQ_Y+2, 3, SQ_H-4);

    var true_square = new createjs.Shape();
    true_square.graphics.beginStroke("green").beginFill("green").drawRect(true_x, SQ_Y+1, 1, SQ_H-2);
    stage.addChild(square);
    stage.addChild(res_square);

    if (IS_FEEDBACK) {stage.addChild(true_square);}

    stage.update();

     //document.getElementById("Target").innerHTML= "Target: " + true_xr + "%";
    document.getElementById("Target").innerHTML= "Target: " + TRUE_RATIO + "%";

    // for debug: eventuall remove this
    if (DEBUG2) {
        document.getElementById("Debug").innerHTML= "Results: " + results + " Result: " + result +
        " Repeats: " + repeats +"/" + MAX_REPATS + " Reaction time: " + reactionTime;
    }


    if (IS_FEEDBACK) {
          if (isCorrect) {
           document.getElementById("Feedback").innerHTML= "You clicked: " + res_xr + "%";

           finished();
           return 0;

        } else {
          document.getElementById("Feedback").innerHTML= "You clicked: " + res_xr + "%" + ". This is not accurate enough. Let's try again.";
          document.getElementById("Feedback").style.color = "red";
          document.getElementById("Counter").innerHTML="You may lose bonus.";
        }
    } else {
        if (isCorrect) {
           document.getElementById("Feedback").innerHTML= "Trial OK.";
           document.getElementById("Feedback").style.color = "green";
           finished();
           return 0;

       } else {
           document.getElementById("Feedback").innerHTML= "This is not accurate enough. Let's try again.";
           document.getElementById("Feedback").style.color = "red";
           document.getElementById("Counter").innerHTML="You may lose bonus.";
       }
    }



    // wait a bit and than redo
    setTimeout(function(){
        if (repeats<MAX_REPATS) {
            if (!isCorrect) {init();}
        }
        else {
            document.getElementById("Feedback").innerHTML= "Ok, let's try something else."
            document.getElementById("Feedback").style.color = "red";
            finished();
            return 0;
        }
    }, WAIT_TIME);
}
