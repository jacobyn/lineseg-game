var SQ_X=20; // begining of square
var SQ_Y=20; // begining of square
var SQ_W=600; // width of square
var SQ_H=100; // height of square
var SQ_R=3; //roundness of square (aethtetics)
var PROX_T=11;

// inputs:
var TRUE_RATIO=NaN; // input
var IS_FEEDBACK=true; //give feedback?

var WAIT_TIME=2000; // in between trials wait time
var MAX_TIME_TRIAL=10*1000;
var MAX_REPATS=3;   // maximal number of repetiotions to try find correct response

var DEBUG=true; // plot internal variables (for debug puropose)

// outputs:
var results=[]; //output list
var result;    //the final output (NaN if incorrect)
var repeats=0; //number of repeats
var reactionTime=0;
var timeStarted;
var stage; // global variable holding the stage (canvas)
//var d = new Date();



create_agent = function() {
    reqwest({
        url: "/node/" + uniqueId,
        method: 'post',
        type: 'json',
        success: function (resp) {

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
                window.location = "/debrief/1?hit_id=" + hit_id + "&assignment_id=" + assignment_id + "&worker_id=" + worker_id + "&mode=" + mode;
            }
        }
    });
};

function getIsPractice() {
   reqwest ({
        url: "/is_practice/" + my_network_id,
        method: 'get',
        type: 'json',
        success: function (resp) {
            IS_FEEDBACK = resp.is_practice;
            startInit();
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
}


// get the seed from server:
function startInit() {
    reqwest ({
        url: "/node/" + my_node_id + "/received_infos",
        method: 'get',
        type: 'json',
        success: function (resp) {
            TRUE_RATIO=Number(resp.infos[0].contents)
             init();
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


// draw things on the screen
function init() {
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
    document.getElementById("Feedback").innerHTML="Segment the square according to the target's percentage:"
    currentRepeat=repeats;
    setInterval(function(){timeOver(currentRepeat)},MAX_TIME_TRIAL);
}

// send result to server
function finished(){
   // var output = {"results": results.toString(), "result": result.toString(), "repeats": repeats.toString(), reactionTime:reactionTime.toString(), "TRUE_RATIO": TRUE_RATIO}
   // //console.log(output);
    reqwest({
        url: "/info/" + my_node_id,
        method: 'post',
        type: 'json',
        data: {
            contents: result,
            property1: repeats, // number of failed trials
            property2: reactionTime, // bandit_id
            property3: TRUE_RATIO, // remembered
            property4: results.toString(),
        },
        success: function (resp) {
            setTimeout(function(){allow_exit();location.reload(true);},WAIT_TIME);
        }
    });
}

// cant wait so long... abort and send NaN result
function timeOver(current_repeat) {
    if (current_repeat!=repeats){return;}
    document.getElementById("Feedback").innerHTML= "Time over! You only have " + Math.round(MAX_TIME_TRIAL/1000) + " seconds to complete the trial!";
    document.getElementById("Feedback").style.color = "red";
    result="NaN";results.push(result);


    reactionTime=performance.now()-timeStarted;
    var square = new createjs.Shape();
    square.graphics.setStrokeStyle(5).beginStroke("red").beginFill("gray").drawRoundRect(SQ_X, SQ_Y, SQ_W, SQ_H,SQ_R,SQ_R,SQ_R,SQ_R);
    stage.addChild(square);
    stage.update();


    finished();
}

  // Click happenened: manage interface
function handleClick(event){

   reactionTime=performance.now()-timeStarted;

   res_x= event.stageX;
   res_xr=Math.round(100*(res_x-SQ_X)/SQ_W);
   true_xr=TRUE_RATIO;
   true_x=SQ_X+SQ_W*Math.round(true_xr)/100;
   var isCorrect=false;
   results.push(res_xr);

   if (Math.abs(res_xr-true_xr)<PROX_T) {
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

  if (IS_FEEDBACK) {
      if (isCorrect) {
       document.getElementById("Feedback").innerHTML= "You clicked: " + res_xr + " %";

        finished();

   } else {
       document.getElementById("Feedback").innerHTML= "You clicked: " + res_xr + " %" + ". This is not accurate enought. Let's try again...";
       document.getElementById("Feedback").style.color = "red";
   }
} else {
    if (isCorrect) {
       document.getElementById("Feedback").innerHTML= "Trial OK.";
       document.getElementById("Feedback").style.color = "green";
       finished()

   } else {
       document.getElementById("Feedback").innerHTML= "This is not accurate enought. Let's try again...";
       document.getElementById("Feedback").style.color = "red";
   }
}


    document.getElementById("Target").innerHTML= "Target: " + true_xr + " %";
    document.getElementById("Target").innerHTML= "Target: " + TRUE_RATIO + " % ";
    // wait a bit and than redo
    setTimeout(function(){

    if (repeats<MAX_REPATS) {
        if (!isCorrect) {init();}

    }
    else {
    document.getElementById("Feedback").innerHTML= "Ok, let's try something else..."
       document.getElementById("Feedback").style.color = "red";

        finished();
    }

}, WAIT_TIME);

// for debug: eventuall remove this
    if (DEBUG) {


        document.getElementById("Debug").innerHTML= "Results: " + results.toString() + " Result: " + result +
        " Repeats: " + repeats +"/" + MAX_REPATS + "reaction time: " + reactionTime;
    }
}
