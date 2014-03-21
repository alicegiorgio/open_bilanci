/**
 * Created by stefano on 3/21/14.
 */
var url_is_correct = false;

function setIndicatorLinksUrl(){
    var territorio_1_slug = $("#id_territorio_1").select2("val");
    var territorio_2_slug = $("#id_territorio_2").select2("val");

    var url = '/confronti/'+territorio_1_slug+"/"+territorio_2_slug;
    //gets all the link in the parameter side menu
    var parameters = $('.confronti_parameter_container li a');

    //sets the link for indicators in the menu as
    // confronti/territorio1/territorio2/typeofindicator/indicator-slug

    $.each(parameters, function(index, value) {
        var indicator_id = this.id;

        var newLink = url + "/" + indicator_id;
        $(value).attr('href', newLink);
    });

}

function setSubmitButtonUrl(){

    var territorio_1_slug = $("#id_territorio_1").select2("val");
    var territorio_2_slug = $("#id_territorio_2").select2("val");

    var url = '/confronti/'+territorio_1_slug+"/"+territorio_2_slug;

    $("#confronti_submit_btn").attr("href", url);
}

function changeConfrontiDataUrl(){

    var territorio_1_slug = $("#id_territorio_1").select2("val");
    var territorio_2_slug = $("#id_territorio_2").select2("val");

    if(territorio_1_slug && territorio_2_slug){

        //sets url for the fake submit button
        setSubmitButtonUrl();

        // sets url for indicatori link in the side menu
        setIndicatorLinksUrl();

        url_is_correct = true;
    }
    else{

        url_is_correct = false;
    }
}


function changeConfrontiHomeUrl(){
            var territorio_1_slug = $("#id_territorio_1").select2("val");
            var territorio_2_slug = $("#id_territorio_2").select2("val");

            if(territorio_1_slug && territorio_2_slug){

                //sets url for the fake submit button
                var url = '/confronti/'+territorio_1_slug+"/"+territorio_2_slug+"";
                $("#confronti_submit_btn").attr("href", url);
                url_is_correct = true;
            }
            else{

                url_is_correct = false;
            }
        }

function submitButtonConfronti(e){
     e.preventDefault();

    //if url is correct, navigates to confronti page, else display error msg

    if(url_is_correct)
    {
        window.location = $("#confronti_submit_btn").attr('href');
    }
    else{
        //insert error text
        $( "#error_msg_box_txt" ).html('ATTENZIONE, DEVI SELEZIONARE DUE COMUNI PER PROCEDERE NEL CONFRONTO')
        //show error_msg_box
        $("#error_msg_box").removeClass('hidden');

    }
}