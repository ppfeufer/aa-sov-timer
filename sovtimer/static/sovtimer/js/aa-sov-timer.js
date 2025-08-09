/* global sovtimerJsSettingsDefaults, sovtimerJsSettingsOverride, moment, objectDeepMerge, fetchGet */

$(document).ready(() => {
    'use strict';

    // Build the settings object
    let sovtimerSettings = sovtimerJsSettingsDefaults;

    if (typeof sovtimerJsSettingsOverride !== 'undefined') {
        sovtimerSettings = objectDeepMerge(
            sovtimerJsSettingsDefaults,
            sovtimerJsSettingsOverride
        );
    }

    const elementTimerTotal = $('.aa-sovtimer-campaigns-total');
    const elementTimerUpcoming = $('.aa-sovtimer-campaigns-upcoming');
    const elementTimerActive = $('.aa-sovtimer-campaigns-active');

    /**
     * Convert seconds into a time string
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

            secondsRemaining = Math.abs(secondsRemaining); // Remove negative prefix

            secondsRemaining++; // Increment with one second each second
        } else {
            secondsRemaining--; // Decrement with one second each second
        }

        const days = Math.floor(secondsRemaining / (24 * 60 * 60)); // Calculate days
        let hours = Math.floor(secondsRemaining / (60 * 60)) % 24; // Hours
        let minutes = Math.floor(secondsRemaining / 60) % 60; // Minutes
        let seconds = Math.floor(secondsRemaining) % 60; // Seconds

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
            countdown: `<span class="${spanClasses}">${prefix}${days}d ${hours}h ${minutes}m ${seconds}s</span>`,
            remainingTimeInSeconds: prefix + secondsRemaining
        };
    };

    /**
     * Build the datatable
     *
     * @type {jQuery}
     */
    const sovCampaignTable = $('.aa-sovtimer-campaigns');

    fetchGet({url: sovtimerSettings.url.ajaxUpdate})
        .then((tableData) => {
            if (tableData) {
                sovCampaignTable.DataTable({
                    language: sovtimerSettings.dataTables.language,
                    data: tableData,
                    columns: [
                        // Column: 0
                        {
                            data: 'event_type'
                        },

                        // Column: 1
                        {
                            data: 'solar_system_name_html'
                        },

                        // Column: 2
                        {
                            data: 'constellation_name_html'
                        },

                        // Column: 3
                        {
                            data: 'region_name_html'
                        },

                        // Column: 4
                        {
                            data: 'defender_name_html'
                        },

                        // Column: 5
                        {
                            data: 'adm'
                        },

                        // Column: 6
                        {
                            data: 'start_time',
                            render: {
                                _: (data) => {
                                    return data === null ? '' : moment(data).utc().format(
                                        sovtimerSettings.datetimeFormat.datetimeLong
                                    );
                                },
                                sort: (data) => {
                                    return data === null ? '' : data;
                                }
                            }
                        },

                        // Column: 7
                        {
                            data: 'remaining_time'
                        },

                        // Column: 8
                        {
                            data: 'campaign_progress'
                        },

                        // Hidden columns
                        // Column: 9
                        {
                            data: 'remaining_time_in_seconds'
                        },

                        // Column: 10
                        {
                            data: 'solar_system_name'
                        },

                        // Column: 11
                        {
                            data: 'constellation_name'
                        },

                        // Column: 12
                        {
                            data: 'region_name'
                        },

                        // Column: 13
                        {
                            data: 'defender_name'
                        },

                        // Column: 14
                        {
                            data: 'active_campaign'
                        }
                    ],
                    columnDefs: [
                        {
                            visible: false,
                            targets: [0, 9, 10, 11, 12, 13, 14]
                        },
                        // {
                        //     width: '115px',
                        //     targets: [7]
                        // },
                        {
                            width: '150px',
                            targets: [8]
                        }
                    ],
                    order: [[6, 'asc']],
                    filterDropDown: {
                        columns: [
                            // Filter: Type
                            // {
                            //     idx: 0,
                            //     title: sovtimerSettings.translation.dtFilter.type
                            // },

                            // Filter: System
                            {
                                idx: 10,
                                title: sovtimerSettings.translation.dtFilter.system
                            },

                            // Filter: Constellation
                            {
                                idx: 11,
                                title: sovtimerSettings.translation.dtFilter.constellation
                            },

                            // Filter: Region
                            {
                                idx: 12,
                                title: sovtimerSettings.translation.dtFilter.region
                            },

                            // Filter: Owner/Defender
                            {
                                idx: 13,
                                title: sovtimerSettings.translation.dtFilter.owner
                            },

                            // Filter: Active Campaign
                            {
                                idx: 14,
                                title: sovtimerSettings.translation.dtFilter.activeCampaign
                            }
                        ],
                        autoSize: false,
                        bootstrap: true,
                        bootstrap_version: 5
                    },
                    createdRow: (row, data) => {
                        // Total timer
                        const currentTotal = elementTimerTotal.html();
                        const newTotal = parseInt(currentTotal) + 1;

                        elementTimerTotal.html(newTotal);

                        // Upcoming timer (< 4 hrs)
                        if (data.active_campaign === sovtimerSettings.translation.no && data.remaining_time_in_seconds <= sovtimerSettings.upcomingTimerThreshold) {
                            $(row).addClass('aa-sovtimer-upcoming-campaign');

                            const currentUpcoming = elementTimerUpcoming.html();
                            const newUpcoming = parseInt(currentUpcoming) + 1;

                            elementTimerUpcoming.html(newUpcoming);
                        }

                        // Active timer
                        if (data.active_campaign === sovtimerSettings.translation.yes) {
                            $(row).addClass('aa-sovtimer-active-campaign');

                            const currentActive = elementTimerActive.html();
                            const newActive = parseInt(currentActive) + 1;

                            elementTimerActive.html(newActive);
                        }
                    },
                    paging: false
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching campaign data:', error);
        });

    /**
     * Update the datatable information every 30 seconds
     */
    setInterval(() => {
        fetchGet({url: sovtimerSettings.url.ajaxUpdate})
            .then((newData) => {
                const dataTable = sovCampaignTable.DataTable();
                dataTable.clear().rows.add(newData).draw();

                let totalCount = 0;
                let upcomingCount = 0;
                let activeCount = 0;

                newData.forEach((item) => {
                    totalCount++;

                    if (item.active_campaign === sovtimerSettings.translation.no && item.remaining_time_in_seconds <= sovtimerSettings.upcomingTimerThreshold) {
                        upcomingCount++;
                    }

                    if (item.active_campaign === sovtimerSettings.translation.yes) {
                        activeCount++;
                    }
                });

                elementTimerTotal.html(totalCount);
                elementTimerUpcoming.html(upcomingCount);
                elementTimerActive.html(activeCount);
            })
            .catch((error) => {
                console.error('Error updating campaign data:', error);
            });
    }, 30000);

    /**
     * Update the remaining time every second
     */
    setInterval(() => {
        sovCampaignTable.DataTable().rows().every((element) => {
            const data = sovCampaignTable.DataTable().row(element).data();

            const remaining = secondsToRemainingTime(
                data.remaining_time_in_seconds
            );

            data.remaining_time_in_seconds = remaining.remainingTimeInSeconds;
            data.remaining_time = remaining.countdown;

            sovCampaignTable.DataTable().row(element).data(data);
        });
    }, 1000);
});
