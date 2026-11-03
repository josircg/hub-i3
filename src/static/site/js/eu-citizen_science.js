const CardManager = {
    clickOnHeart: function(object_id, url){
        let beforeSend = $.ajaxSettings.beforeSend;
        let $element = $('#heart'+object_id);

        $.ajax({
            type: 'POST',
            url: url,
            data: {object_id: object_id},
            beforeSend: function(xhr, settings) {
                beforeSend(xhr, settings);

                if($element.is( ":button" )){
                   $element.find('i').toggleClass('far fa-heart fas fa-spinner fa-spin');
                }
            },
            success: function(response){
                console.log(response);

                if($element.is( ":button" )){
                    $element.toggleClass('btn-my-darkBlue btn-my-outline-darkBlue');
                    $element.find('i').toggleClass('far fa-heart fas fa-spinner fa-spin');
                } else {
                    let hijo = $element.find(".value")
                    let valor = parseInt(hijo.text(), 10);

                    if (response['Liked'] === true) {
                        $element.addClass("animate__animated animate__fadeIn text-danger")
                        $element.removeClass("text-muted")
                        valor++;
                        $element.one("animationend", function () {
                            $element.removeClass("animate__animated animate__fadeIn ");
                        });
                    } else {
                        $element.addClass("animate__animated animate__fadeIn text-muted")
                        $element.removeClass("text-danger")
                        valor--;
                        $element.one("animationend", function () {
                            $element.removeClass("animate__animated animate__fadeIn");
                        });
                    }
                    hijo.text(valor);
                }
            },
            error: function(response){
                console.log(response)
            },
            complete: function(){
                $element.data('requestRunning', false);
            }
        })
    },

    clickOnFollow: function(object_id, url){
        let beforeSend = $.ajaxSettings.beforeSend;
        let $element = $('#follow'+object_id);

        $.ajax({
            type: 'POST',
            url: url,
            data: {object_id: object_id},
            beforeSend: function(xhr, settings) {
                beforeSend(xhr, settings);

                if($element.is( ":button" )){
                   $element.find('i').toggleClass('far fa-bookmark fas fa-spinner fa-spin');
                }
            },
            success: function(response){
                console.log(response);

                if($element.is( ":button" )){
                    $element.toggleClass('btn-my-darkBlue btn-my-outline-darkBlue');
                    $element.find('i').toggleClass('far fa-bookmark fas fa-spinner fa-spin');
                } else {
                    let hijo = $element.find(".value");
                    let valor = parseInt(hijo.text(), 10);

                    if (response['Followed'] === true) {
                        $element.addClass("animate__animated animate__fadeIn text-primary");
                        $element.removeClass("text-muted");
                        valor++;
                        $element.one("animationend", function () {
                            $element.removeClass("animate__animated animate__fadeIn ");
                        });
                    } else {
                        $element.addClass("animate__animated animate__fadeIn text-muted")
                        $element.removeClass("text-primary")
                        valor--;
                        $element.one("animationend", function () {
                            $element.removeClass("animate__animated animate__fadeIn");
                        });
                    }
                    hijo.text(valor);
                }
            },
            error: function(response){
                console.log(response)
            },
            complete: function(){
                $element.data('requestRunning', false);
            }
        })
    }
};

$(document).ready(function() {
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader('X-CSRFToken', getCSRFToken());
        }
    });
    $(".heart, .heartButton").on("click", function() {
        // Código que se ejecutará cuando se haga clic en el elemento con el ID "mi-boton"
        console.log("heart clicked");
        let $element = $(this);
        console.log($element.data('requestRunning'));

        if ($element.data('requestRunning')){
            console.log('request running');
            return;
        }

        $element.data('requestRunning', true);
        CardManager.clickOnHeart($element.data('object_id'), $element.data('url'));
    });
    $(".followIcon, .followButton").on("click", function() {
        // Código que se ejecutará cuando se haga clic en el elemento con el ID "mi-boton"
        console.log("follow clicked");
        let $element = $(this);
        console.log($element.data('requestRunning'));

        if ($element.data('requestRunning')){
            console.log('request running');
            return;
        }

        $element.data('requestRunning', true);
        CardManager.clickOnFollow($element.data('object_id'), $element.data('url'));
    });

    $('.copyLink').on('click', async function(event) {
        event.preventDefault();
        const link = $(this).data('url');
        console.log('jere');
        try {
          await navigator.clipboard.writeText(link);
        } catch (err) {
          console.error('Error copying link: ', err);
        }
    });

    $('.social-network').on('click', function(event) {
        event.preventDefault();
        const win = window.open($(this).attr('href'),
            '_blank', 'height=500,width=800,resizable=yes,scrollbars=yes');
        win.focus();
    });
});

$(function() {
    $('.doModalAction').click(function(){
        console.log($(this).attr('id'))
        var action=$(this).attr('id')
        if(action == 'deletePlatform'){
            var actionFriend='delete this platform'
            var buttonAction='<button type="button" class="btn btn-danger" id="deletePlatformButton">Yes!, delete it</button>'
        }
        $('#myModalTitle').html('Are you sure you want to '+actionFriend+'?')
        $('#myModalBody').html('Caution!, this is permanent and can not be undone')
        $('#myModalFooter').html(
            buttonAction+
            '<button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>'
        )
        $('#myModal').modal('toggle')

        if(action == 'deletePlatform'){
            attatchDeletePlatform()
        }
    })
    $(document).on('click', '.redirect', function(){
        console.log('redirect')
        window.location.href=$(this).val()
    })
    $(document).on('click', '.close', function(){
        $(this).parent().hide()
    })
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
})

function attatchDeletePlatform(){
    $('#deletePlatformButton').click(function(){
        console.log('Deleted')
        console.log($('#Id').attr('id'))
        $.ajax({
            type: 'GET',
            url: '/deletePlatformAjax/'+$('#Id').val(),
            data: {id: $('Id').attr('id')},
            success: function(response){
                $('#myModalTitle').html('The platform was deleted')
                $('#myModalBody').html('You can close this window')
                $('#myModalFooter').html('<button type="button" class="btn btn-secondary redirect" value="/platforms" data-dismiss="modal" >Close</button>')

            },
            error: function(response){
                $('#myModalBody').html('Ops, something went wrong')
                $('#deletePlatformButton').hide()

            }
        })
    })
}

class ProjectStatsChart {
    constructor(config) {
        this.accessLabel = config.accessLabel || 'Accesses';
        this.likesLabel = config.likesLabel || 'Likes';
        this.followsLabel = config.followsLabel || 'Follows';
        this.locale = config.locale || 'en';
        this.chartTitle = config.chartTitle || 'Stats';
        this.xaxisTitle = config.xaxisTitle || 'Days';
        this.yaxisTitle = config.yaxisTitle || 'Values';
    }

    createChart(labels, accesses, likes, follows, div_id) {
        // Define chart data
        let data = [
            {
                x: labels,
                y: accesses,
                type: 'bar',
                name: this.accessLabel,
                text: accesses.map(String),
                textposition: 'auto',
                marker: {color: 'rgba(75, 192, 192, 0.2)'}
            },
            {
                x: labels,
                y: likes,
                type: 'bar',
                name: this.likesLabel,
                text: likes.map(String),
                textposition: 'auto',
                marker: {color: 'rgba(255, 99, 132, 0.2)'}
            },
            {
                x: labels,
                y: follows,
                type: 'bar',
                name: this.followsLabel,
                text: follows.map(String),
                textposition: 'auto',
                marker: {color: 'rgba(255, 206, 86, 0.2)'}
            }
        ];
        // Define the chart layout
        let layout = {
            title: this.chartTitle,
            xaxis: { title: this.xaxisTitle },
            yaxis: { title: this.yaxisTitle }
        };
        // Render the chart in the specified div
        Plotly.newPlot(div_id, data, layout, {
            scrollZoom: true,
            displaylogo: false,
            responsive: true,
            locale: this.locale,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        });
    }

    generateProjectStats(project_id, div_id) {
        $.ajax({
            type: 'POST',
            url: '/generate_project_stats_ajax',
            dataType: 'json',
            data: {project_id: project_id},
            success: (response) => {
                console.log(response);
                console.log(typeof(response));
                if (response.length){
                    let days = [];
                    let accesses = [];
                    let likes = [];
                    let follows = [];
                    $.each(response, (key, value) => {
                        days.push(value['day']);
                        accesses.push(value['accesses']);
                        likes.push(value['likes']);
                        follows.push(value['follows']);
                    });
                    this.createChart(days, accesses, likes, follows, 'project_chart_' + project_id);
                    $('#' + div_id).show();
                }
            },
            error: (response) => {
                console.log(response);
            }
        })
    }
}