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

    const elements = {
        campaignsTotal: $('.aa-sovtimer-campaigns-total'),
        campaignsUpcoming: $('.aa-sovtimer-campaigns-upcoming'),
        campaignsActive: $('.aa-sovtimer-campaigns-active')
    };

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
            secondsRemaining = Math.abs(secondsRemaining) + 1;
        } else {
            secondsRemaining--;
        }

        const days = Math.floor(secondsRemaining / 86400);
        const hours = String(Math.floor(secondsRemaining / 3600) % 24).padStart(2, '0');
        const minutes = String(Math.floor(secondsRemaining / 60) % 60).padStart(2, '0');
        const seconds = String(Math.floor(secondsRemaining) % 60).padStart(2, '0');

        return {
            countdown: `<span class="${spanClasses}">${prefix}${days}d ${hours}h ${minutes}m ${seconds}s</span>`,
            remainingTimeInSeconds: prefix + secondsRemaining
        };
    };

    /**
     * Build the DataTable
     *
     * @type {jQuery}
     */
    const sovCampaignTable = $('.aa-sovtimer-campaigns');

    fetchGet({url: sovtimerSettings.url.ajaxUpdate})
        .then((tableData) => {
            if (tableData) {
                // Destroy any existing DataTable
                // if ($.fn.dataTable.isDataTable(sovCampaignTable)) {
                //     sovCampaignTable.DataTable().destroy();
                // }

                // Create the DataTable
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
                        // Increment total timer
                        elements.campaignsTotal.html(parseInt(elements.campaignsTotal.html()) + 1);

                        // Upcoming timer (< 4 hrs)
                        if (
                            data.active_campaign === sovtimerSettings.translation.no
                            && data.remaining_time_in_seconds <= sovtimerSettings.upcomingTimerThreshold // jshint ignore:line
                        ) {
                            $(row).addClass('aa-sovtimer-upcoming-campaign');

                            elements.campaignsUpcoming.html(parseInt(elements.campaignsUpcoming.html()) + 1);
                        }

                        // Active timer
                        if (data.active_campaign === sovtimerSettings.translation.yes) {
                            $(row).addClass('aa-sovtimer-active-campaign');

                            elements.campaignsActive.html(parseInt(elements.campaignsActive.html()) + 1);
                        }
                    },
                    paging: false,
                    initComplete: () => {
                        /**
                         * Update the remaining time every second
                         */
                        setInterval(() => {
                            const dt = sovCampaignTable.DataTable();

                            dt.rows().every((index) => {
                                const row = dt.row(index);
                                const remaining = secondsToRemainingTime(row.data().remaining_time_in_seconds);

                                row.data({
                                    ...row.data(),
                                    remaining_time_in_seconds: remaining.remainingTimeInSeconds,
                                    remaining_time: remaining.countdown
                                });
                            });
                        }, 1000);

                        /**
                         * Update the datatable information every 30 seconds
                         */
                        setInterval(() => {
                            fetchGet({url: sovtimerSettings.url.ajaxUpdate})
                                .then((newData) => {
                                    sovCampaignTable.DataTable().clear().rows.add(newData).draw();

                                    const counts = newData.reduce(
                                        (acc, item) => {
                                            acc.total++;

                                            if (
                                                item.active_campaign === sovtimerSettings.translation.no
                                                && item.remaining_time_in_seconds <= sovtimerSettings.upcomingTimerThreshold // jshint ignore:line
                                            ) {
                                                acc.upcoming++;
                                            }

                                            if (item.active_campaign === sovtimerSettings.translation.yes) {
                                                acc.active++;
                                            }

                                            return acc;
                                        },
                                        { total: 0, upcoming: 0, active: 0 }
                                    );

                                    elements.campaignsTotal.html(counts.total);
                                    elements.campaignsUpcoming.html(counts.upcoming);
                                    elements.campaignsActive.html(counts.active);
                                })
                                .catch((error) => {
                                    console.error('Error updating campaign data:', error);
                                });
                        }, 30000);
                    }
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching campaign data:', error);
        });
});
