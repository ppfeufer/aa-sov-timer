/* global sovtimerJsSettingsDefaults, sovtimerJsSettingsOverride, moment, objectDeepMerge, fetchGet, DataTable */

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
     * Remove search from column control.
     *
     * @param {Array} columnControl
     * @param {int} index
     * @return {Array}
     * @private
     */
    const _removeSearchFromColumnControl = (columnControl, index = 1) => {
        const cc = JSON.parse(JSON.stringify(columnControl));

        if (cc[index]) {
            cc[index].content = [];
        }

        return cc;
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
                console.log($('.navbar.fixed-top').height());
                // Destroy any existing DataTable
                // if ($.fn.dataTable.isDataTable(sovCampaignTable)) {
                //     sovCampaignTable.DataTable().destroy();
                // }

                // Create the DataTable
                const dt = new DataTable(sovCampaignTable, { // eslint-disable-line no-unused-vars
                    language: sovtimerSettings.dataTables.language,
                    data: tableData,
                    dom: sovtimerSettings.dataTables.dom,
                    ordering: sovtimerSettings.dataTables.ordering,
                    columnControl: sovtimerSettings.dataTables.columnControl,
                    columns: [
                        // Column: 0
                        {
                            // data: 'solar_system_name_html'
                            data: {
                                display: (data) => {
                                    return data.solar_system_name_html;
                                },
                                sort: (data) => {
                                    return data.solar_system_name;
                                },
                                filter: (data) => {
                                    return data.solar_system_name;
                                }
                            }
                        },

                        // Column: 1
                        {
                            // data: 'constellation_name_html'
                            data: {
                                display: (data) => {
                                    return data.constellation_name_html;
                                },
                                sort: (data) => {
                                    return data.constellation_name;
                                },
                                filter: (data) => {
                                    return data.constellation_name;
                                }
                            }
                        },

                        // Column: 2
                        {
                            // data: 'region_name_html'
                            data: {
                                display: (data) => {
                                    return data.region_name_html;
                                },
                                sort: (data) => {
                                    return data.region_name;
                                },
                                filter: (data) => {
                                    return data.region_name;
                                }
                            }
                        },

                        // Column: 3
                        {
                            // data: 'defender_name_html'
                            data: {
                                display: (data) => {
                                    return data.defender_name_html;
                                },
                                sort: (data) => {
                                    return data.defender_name;
                                },
                                filter: (data) => {
                                    return data.defender_name;
                                }
                            }
                        },

                        // Column: 4
                        {
                            data: 'adm'
                        },

                        // Column: 5
                        {
                            // data: 'start_time'
                            data: {
                                display: (data) => {
                                    return data.start_time === null ? '' : moment(data.start_time).utc().format(
                                        sovtimerSettings.datetimeFormat.datetimeLong
                                    );
                                },
                                sort: (data) => {
                                    return data.start_time === null ? '' : data.start_time;
                                },
                                filter: (data) => {
                                    return data.start_time === null ? '' : data.start_time;
                                }
                            }
                        },

                        // Column: 6
                        {
                            // data: 'remaining_time'
                            data: {
                                display: (data) => {
                                    return data.remaining_time;
                                },
                                sort: (data) => {
                                    return parseInt(data.remaining_time_in_seconds, 10);
                                },
                                filter: (data) => {
                                    return parseInt(data.remaining_time_in_seconds, 10);
                                }
                            }
                        },

                        // Column: 7
                        {
                            // data: 'campaign_progress'
                            data: {
                                display: (data) => {
                                    return data.campaign_progress;
                                },
                                sort: (data) => {
                                    return data.campaign_progress;
                                },
                                filter: (data) => {
                                    return data.active_campaign;
                                }
                            }
                        },
                    ],
                    columnDefs: [
                        {
                            targets: [4, 5, 6, 7],
                            columnControl: _removeSearchFromColumnControl(sovtimerSettings.dataTables.columnControl, 1)
                        },
                        {
                            target: 6,
                            type: 'string',
                            width: 175
                        },
                        {
                            target: 7,
                            type: 'string',
                            width: 175
                        }
                    ],
                    order: [[5, 'asc']],
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
