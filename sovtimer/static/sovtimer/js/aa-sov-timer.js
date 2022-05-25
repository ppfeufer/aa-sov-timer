/* global aaSovtimerSettings, moment */

$(document).ready(() => {
    'use strict';

    const elementTimerTotal = $('.aa-sovtimer-timers-total');
    const elementTimerUpcoming = $('.aa-sovtimer-timers-upcoming');
    const elementTimerActive = $('.aa-sovtimer-timers-active');

    /**
     * convert seconds into a time string
     *
     * @param {string|int} secondsRemaining
     * @returns {{countdown: string, remainingTimeInSeconds: string|int}}
     */
    const secondsToRemainingTime = (secondsRemaining) => {
        let prefix = '';
        let spanClasses = 'aa-sovtimer-remaining';

        if (secondsRemaining < 0) {
            spanClasses += ' aa-sovtimer-timer-elapsed';
            prefix = '-';

            secondsRemaining = Math.abs(secondsRemaining); // remove negative prefix

            secondsRemaining++; // increment with one second each second
        } else {
            secondsRemaining--; // decrement with one second each second
        }

        const days = Math.floor(secondsRemaining / (24 * 60 * 60)); // calculate days
        let hours = Math.floor(secondsRemaining / (60 * 60)) % 24; // hours
        let minutes = Math.floor(secondsRemaining / 60) % 60; // minutes
        let seconds = Math.floor(secondsRemaining) % 60; // seconds

        // leading zero ...
        if (hours < 10) {
            hours = '0' + hours;
        }

        if (minutes < 10) {
            minutes = '0' + minutes;
        }

        if (seconds < 10) {
            seconds = '0' + seconds;
        }

        return {
            countdown: '<span class="' + spanClasses + '">' + prefix + days + 'd ' + hours + 'h ' + minutes + 'm ' + seconds + 's</span>',
            remainingTimeInSeconds: prefix + secondsRemaining
        };
    };

    /**
     * build the datatable
     *
     * @type {jQuery}
     */
    const sovCampaignTable = $('.aa-sovtimer-campaigns').DataTable({
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
                render: (data, type, row) => {
                    return moment(data).utc().format(aaSovtimerSettings.dateformat);
                }
            },
            {
                data: 'remaining_time'
            },
            {
                data: 'campaign_progress'
            },

            // hidden columns
            {
                data: 'remaining_time_in_seconds'
            },
            {
                data: 'solar_system_name'
            },
            {
                data: 'constellation_name'
            },
            {
                data: 'region_name'
            },
            {
                data: 'defender_name'
            },
            {
                data: 'active_campaign'
            }
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
                    idx: 0
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
                }
            ],
            autoSize: false,
            bootstrap: true
        },
        createdRow: (row, data, dataIndex) => {
            // Total timer
            const currentTotal = elementTimerTotal.html();
            const newTotal = parseInt(currentTotal) + 1;

            elementTimerTotal.html(newTotal);

            // Upcoming timer (< 4 hrs)
            if (data.active_campaign === aaSovtimerSettings.translations.no && data.remaining_time_in_seconds <= 14400) {
                $(row).addClass('aa-sovtimer-upcoming-campaign');

                const currentUpcoming = elementTimerUpcoming.html();
                const newUpcoming = parseInt(currentUpcoming) + 1;

                elementTimerUpcoming.html(newUpcoming);
            }

            // Active timer
            if (data.active_campaign === aaSovtimerSettings.translations.yes) {
                $(row).addClass('aa-sovtimer-active-campaign');

                const currentActive = elementTimerActive.html();
                const newActive = parseInt(currentActive) + 1;

                elementTimerActive.html(newActive);
            }
        },
        paging: false
    });

    /**
     * refresh the datatable information every 30 seconds
     */
    setInterval(() => {
        sovCampaignTable.ajax.reload((tableData) => {
            elementTimerTotal.html('0');
            elementTimerUpcoming.html('0');
            elementTimerActive.html('0');

            $.each(tableData, (i, item) => {
                // Total timer
                const currentTotal = elementTimerTotal.html();
                const newTotal = parseInt(currentTotal) + 1;

                elementTimerTotal.html(newTotal);

                // Upcoming timer (< 4 hrs)
                if (item.active_campaign === aaSovtimerSettings.translations.no && item.remaining_time_in_seconds <= 14400) {
                    const currentUpcoming = elementTimerUpcoming.html();
                    const newUpcoming = parseInt(currentUpcoming) + 1;

                    elementTimerUpcoming.html(newUpcoming);
                }

                // Active timer
                if (item.active_campaign === aaSovtimerSettings.translations.yes) {
                    const currentActive = elementTimerActive.html();
                    const newActive = parseInt(currentActive) + 1;

                    elementTimerActive.html(newActive);
                }
            });
        });
    }, 30000);

    /**
     * refresh remaining time every second
     */
    setInterval(() => {
        sovCampaignTable.rows().every(function () {
            const data = this.data();

            const remaining = secondsToRemainingTime(
                data.remaining_time_in_seconds
            );

            data.remaining_time_in_seconds = remaining.remainingTimeInSeconds;
            data.remaining_time = remaining.countdown;

            sovCampaignTable.row(this).data(data);
        });
    }, 1000);
});
