/* global sovtimerJsSettingsDefaults, sovtimerJsSettingsOverride, moment, objectDeepMerge, fetchGet, DataTable */

$(document).ready(() => {
    'use strict';

    const sovtimerSettings = typeof sovtimerJsSettingsOverride !== 'undefined'
        ? objectDeepMerge(sovtimerJsSettingsDefaults, sovtimerJsSettingsOverride) // jshint ignore: line
        : sovtimerJsSettingsDefaults;

    const elements = {
        campaignsTotal: $('.aa-sovtimer-campaigns-total'),
        campaignsUpcoming: $('.aa-sovtimer-campaigns-upcoming'),
        campaignsActive: $('.aa-sovtimer-campaigns-active')
    };

    /**
     * Remove search from column control.
     *
     * @param {Array} columnControl Column control.
     * @param {int} index Index of the column to remove search from.
     * @return {Array} Modified column control.
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
     * Convert seconds to remaining time format.
     *
     * @param {string | int | float} secondsRemaining
     * @return {{countdown: string, remainingTimeInSeconds: string | int}} Object with countdown HTML and remaining time in seconds.
     * @private
     */
    const _secondsToRemainingTime = (secondsRemaining) => {
        const isElapsed = secondsRemaining < 0;
        const prefix = isElapsed ? '-' : '';
        const spanClasses = `aa-sovtimer-remaining${isElapsed ? ' aa-sovtimer-timer-elapsed' : ''}`;

        secondsRemaining = Math.abs(secondsRemaining) + (isElapsed ? 1 : -1);

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
     * Update campaign counts.
     *
     * @param {Object} data Campaign data.
     * @private
     */
    const _updateCampaignCounts = (data) => {
        const counts = data.reduce((campaigns, item) => {
            campaigns.total++;

            if (
                item.active_campaign === sovtimerSettings.translation.no
                && item.remaining_time_in_seconds <= sovtimerSettings.upcomingTimerThreshold // jshint ignore:line
            ) {
                campaigns.upcoming++;
            }

            if (item.active_campaign === sovtimerSettings.translation.yes) {
                campaigns.active++;
            }

            return campaigns;
        }, {total: 0, upcoming: 0, active: 0});

        elements.campaignsTotal.html(counts.total);
        elements.campaignsUpcoming.html(counts.upcoming);
        elements.campaignsActive.html(counts.active);
    };

    const sovCampaignTable = $('.aa-sovtimer-campaigns');

    fetchGet({url: sovtimerSettings.url.ajaxUpdate})
        .then((tableData) => {
            if (!tableData) {
                return;
            }

            const dt = new DataTable(sovCampaignTable, { // eslint-disable-line no-unused-vars
                language: sovtimerSettings.dataTables.language,
                data: tableData,
                dom: sovtimerSettings.dataTables.dom,
                ordering: sovtimerSettings.dataTables.ordering,
                columnControl: sovtimerSettings.dataTables.columnControl,
                columns: [
                    // Column: 0 - System
                    {
                        data: {
                            display: d => d.solar_system_name_html,
                            sort: d => d.solar_system_name,
                            filter: d => d.solar_system_name
                        }
                    },
                    // Column: 1 - Constellation
                    {
                        data: {
                            display: d => d.constellation_name_html,
                            sort: d => d.constellation_name,
                            filter: d => d.constellation_name
                        }
                    },
                    // Column: 2 - Region
                    {
                        data: {
                            display: d => d.region_name_html,
                            sort: d => d.region_name,
                            filter: d => d.region_name
                        }
                    },
                    // Column: 3 - Defender
                    {
                        data: {
                            display: d => d.defender_name_html,
                            sort: d => d.defender_name,
                            filter: d => d.defender_name
                        }
                    },
                    // Column: 4 - Activity Defense Multiplier
                    {
                        data: 'adm'
                    },
                    // Column: 5 - Start Time
                    {
                        data: {
                            display: d => d.start_time ? moment(d.start_time).utc().format(sovtimerSettings.datetimeFormat.datetimeLong) : '',
                            sort: d => d.start_time || '',
                            filter: d => d.start_time || ''
                        }
                    },
                    // Column: 6 - Remaining Time
                    {
                        data: {
                            display: d => d.remaining_time,
                            sort: d => parseInt(d.remaining_time_in_seconds, 10),
                            filter: d => parseInt(d.remaining_time_in_seconds, 10)
                        }
                    },
                    // Column: 7 - Campaign Progress
                    {
                        data: {
                            display: d => d.campaign_progress,
                            sort: d => d.campaign_progress,
                            filter: d => d.active_campaign
                        }
                    }
                ],
                columnDefs: [
                    {
                        targets: [4, 5, 6, 7],
                        columnControl: _removeSearchFromColumnControl(sovtimerSettings.dataTables.columnControl, 1)
                    },
                    {target: 6, type: 'string', width: 175},
                    {target: 7, type: 'string', width: 175}
                ],
                order: [[5, 'asc']],
                createdRow: (row, data) => {
                    // Upcoming timer (< 4 hrs)
                    if (
                        data.active_campaign === sovtimerSettings.translation.no
                        && data.remaining_time_in_seconds <= sovtimerSettings.upcomingTimerThreshold // jshint ignore: line
                    ) {
                        $(row).addClass('aa-sovtimer-upcoming-campaign');
                    }

                    // Active timer
                    if (data.active_campaign === sovtimerSettings.translation.yes) {
                        $(row).addClass('aa-sovtimer-active-campaign');
                    }
                },
                paging: false,
                initComplete: () => {
                    // Get DataTable instance
                    const dt = sovCampaignTable.DataTable();

                    // Initial campaign counts update
                    _updateCampaignCounts(dt.rows().data().toArray());

                    // Update the remaining time every second
                    setInterval(() => {
                        dt.rows().every((index) => {
                            const row = dt.row(index);
                            const remaining = _secondsToRemainingTime(row.data().remaining_time_in_seconds);

                            row.data({
                                ...row.data(),
                                remaining_time_in_seconds: remaining.remainingTimeInSeconds,
                                remaining_time: remaining.countdown
                            });
                        });
                    }, 1000);

                    // Update the table data every 30 seconds
                    setInterval(() => {
                        fetchGet({url: sovtimerSettings.url.ajaxUpdate})
                            .then((newData) => {
                                dt.clear().rows.add(newData).draw();
                                _updateCampaignCounts(newData);
                            })
                            .catch(console.error);
                    }, 30000);
                }
            });
        })
        .catch(console.error);
});
