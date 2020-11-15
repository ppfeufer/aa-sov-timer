/* global aaSovtimerSettings, moment */

$(document).ready(function() {
    /**
     * convert seconds into a time string
     *
     * @param secondsRemaining
     * @returns {{countdown: string, remainingTimeInSeconds: int}}
     */
    var secondsToRemainingTime = function(secondsRemaining) {
        var isElapsed = false;
        var prefix = '';
        var countdownHtml = '';
        var returnValue = {};

        if(secondsRemaining < 0) {
            isElapsed = true;
            prefix = '-';

            secondsRemaining = Math.abs(secondsRemaining); // remove negative prefix

            secondsRemaining++; // increment with one second each second
        } else {
            secondsRemaining--; // decrement with one second each second
        }

        var days = Math.floor(secondsRemaining / (24 * 60 * 60)); // calculate days
        var hours = Math.floor(secondsRemaining / (60 * 60)) % 24; // hours
        var minutes = Math.floor(secondsRemaining / 60) % 60; // minutes
        var seconds = Math.floor(secondsRemaining) % 60; // seconds

        // leading zero ...
        if(hours < 10) {
            hours = '0' + hours;
        }

        if(minutes < 10) {
            minutes = '0' + minutes;
        }

        if(seconds < 10) {
            seconds = '0' + seconds;
        }

        if(isElapsed === true) {
            countdownHtml += '<span class="aa-sovtimer-remaining aa-sovtimer-timer-elapsed">';
        } else {
            countdownHtml += '<span class="aa-sovtimer-remaining">';
        }

        countdownHtml += prefix + days + 'd ' + hours + 'h ' + minutes + 'm ' + seconds + 's';
        countdownHtml += '</span>';

        returnValue = {
            remainingTimeInSeconds: prefix + secondsRemaining,
            countdown: countdownHtml
        };

        return returnValue;
    };

    /**
     * build the datatable
     *
     * @type {jQuery}
     */
    var sovCampaignTable = $('.aa-sovtimer-campaigns').DataTable({
        ajax: {
            url: aaSovtimerSettings.url.ajaxUpdate,
            dataSrc: '',
            cache: false
        },
        columns: [
            {
                data: 'event_type'
            },
            {
                data: 'solar_system_name_html'
            },
            {
                data: 'constellation_name_html'
            },
            {
                data: 'region_name_html'
            },
            {
                data: 'defender_name_html'
            },
            {
                data: 'adm'
            },
            {
                data: 'start_time',
                render: $.fn.dataTable.render.moment(moment.ISO_8601, aaSovtimerSettings.dateformat)
            },
            {
                data: 'remaining_time'
            },
            {
                data: 'campaign_progress'
            },

            // hidden columns
            {
                data: 'remaining_time_in_seconds',
            },
            {
                data: 'solar_system_name',
            },
            {
                data: 'constellation_name',
            },
            {
                data: 'region_name',
            },
            {
                data: 'defender_name',
            },
            {
                data: 'active_campaign',
            },
        ],
        columnDefs: [
            {
                visible: false,
                targets: [9, 10, 11, 12, 13, 14]
            },
            {
                width: '150px',
                targets: [8]
            }
        ],
        order: [[6, 'asc']],
        filterDropDown: {
            columns: [
                {
                    idx: 0,
                },
                {
                    idx: 10,
                    title: aaSovtimerSettings.translations.system
                },
                {
                    idx: 11,
                    title: aaSovtimerSettings.translations.constellation
                },
                {
                    idx: 12,
                    title: aaSovtimerSettings.translations.region
                },
                {
                    idx: 13,
                    title: aaSovtimerSettings.translations.owner
                },
                {
                    idx: 14,
                    title: aaSovtimerSettings.translations.activeCampaign
                },
            ],
            autoSize: false,
            bootstrap: true
        },
        createdRow: function(row, data, dataIndex) {
            if(data['active_campaign'] === aaSovtimerSettings.translations.yes) {
                $(row).addClass('aa-sovtimer-active-campaign active');
            }
        },
        paging: false
    });

    /**
     * refresh the datatable information every 30 seconds
     */
    setInterval(function() {
        sovCampaignTable.ajax.reload();
    }, 30000 );

    /**
     * refresh remaining time every second
     */
    setInterval(function() {
        sovCampaignTable.rows().every(function() {
            var d = this.data();

            var remaining = secondsToRemainingTime(d['remaining_time_in_seconds']);

            d['remaining_time_in_seconds'] = remaining.remainingTimeInSeconds;
            d['remaining_time'] = remaining.countdown;

            sovCampaignTable.row(this).data(d);
        });
    }, 1000);
});
