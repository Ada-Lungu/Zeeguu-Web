/**
 * Created by mircea on 09/06/15.
 */

function change_answer_bg_to_white() {
    $("#answer").css({backgroundColor: "white"});
}


function log_new_exercise(outcome) {
    url = ["/gym/create_new_exercise",
        outcome,
         $("#exercise_source").val(),
        -1,
        $("#bookmark_id").val()
        ].join("/");
     $.post(url, function(data) {

     });
}

function iKnowThis() {
    log_new_exercise("I know");
}

function answerIsCorrect(answer, reference) {
    return answer.toLowerCase().trim() == reference.toLowerCase().trim();
}

function checkAnswer() {

    if ($("#answer").val() == "") return;

    if (answerIsCorrect($("#answer").val(), $("#expected_answer").val())) {
        log_new_exercise("Correct");


        $("#check_answer").hide();
        $("#next_exercise").hide().focus().select();
        $("#next").show().focus().select();

        $("#show_solution").hide();
        $("#i_learned_this").show();

        $("#correct_message").show();

        $("#answer").css("color", "green");
        $("#answer").css({backgroundColor: "#c0e38a"});


    } else {
        console.log("checking answer...");
        log_new_exercise("Wrong");
        $("#answer").css({backgroundColor: "#ffdddd"});
        setTimeout(change_answer_bg_to_white, 345);
    }
}

function showAnswer() {
//    $("#question-mark").hide();
//    $("#question-mark-grey").show();
//
//    setTimeout(
//
//        , 345);

    $("#answer").hide();
    $("#expected_answer").show();

    $("#check_answer").hide();
    $("#next_exercise").hide();
    $("#next").show().focus().select();
    $("#show_solution").hide();

    log_new_exercise("Do not know");
//    $("#next_exercise").show().focus().select();

}


