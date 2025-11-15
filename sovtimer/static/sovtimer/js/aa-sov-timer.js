/* global sovtimerJsSettingsDefaults, sovtimerJsSettingsOverride, moment, objectDeepMerge, fetchGet, DataTable, bootstrap */

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
     * Bootstrap tooltip
     *
     * @param {string} [selector=body] Selector for the tooltip elements, defaults to 'body'
     *                                 to apply to all elements with the data-bs-tooltip attribute.
     *                                 Example: 'body', '.my-tooltip-class', '#my-tooltip-id'
     *                                 If you want to apply it to a specific element, use that element's selector.
     *                                 If you want to apply it to all elements with the data-bs-tooltip attribute,
     *                                 use 'body' or leave it empty.
     * @param {string} [namespace=aa-sovtimer] Namespace for the tooltip
     * @returns {void}
     */
    const _bootstrapTooltip = ({selector = 'body', namespace = 'aa-sovtimer'}) => {
        document.querySelectorAll(`${selector} [data-bs-tooltip="${namespace}"]`)
            .forEach((tooltipTriggerEl) => {
                // Dispose existing tooltip instance if it exists
                const existing = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
                if (existing) {
                    existing.dispose();
                }

                // Remove any leftover tooltip elements
                $('.bs-tooltip-auto').remove();

                // Create new tooltip instance
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
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
                language: {url: sovtimerSettings.dataTables.languageUrl},
                data: tableData,
                layout: sovtimerSettings.dataTables.layout,
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
                            filter: d => d.campaign_status
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

                    // Update the remaining time every second
                    // Cache cell nodes and remaining seconds to avoid expensive API calls each tick
                    let _rowCache = dt.rows().indexes().toArray().map((rowIdx) => {
                        const rowData = dt.row(rowIdx).data();

                        return {
                            rowIdx,
                            cellNode: dt.cell(rowIdx, 6).node(),
                            remainingSeconds: Number(rowData.remaining_time_in_seconds)
                        };
                    });

                    /**
                     * Rebuild row cache.
                     *
                     * @private
                     */
                    const _rebuildRowCache = () => {
                        _rowCache = dt.rows().indexes().toArray().map((rowIdx) => {
                            const rowData = dt.row(rowIdx).data();

                            return {
                                rowIdx,
                                cellNode: dt.cell(rowIdx, 6).node(),
                                remainingSeconds: Number(rowData.remaining_time_in_seconds)
                            };
                        });
                    };

                    /**
                     * Tick function to update remaining time.
                     *
                     * @private
                     */
                    const _tick = () => {
                        for (let i = 0; i < _rowCache.length; i++) {
                            const r = _rowCache[i];
                            r.remainingSeconds = Number(r.remainingSeconds) - 1;
                            const remaining = _secondsToRemainingTime(r.remainingSeconds);

                            // Update only the Remaining Time cell DOM (column index 6)
                            if (r.cellNode) {
                                r.cellNode.innerHTML = remaining.countdown;
                            }
                        }
                    };

                    /**
                     * Filter campaigns based on a predicate.
                     *
                     * @param {string} selector The selector for the filter button.
                     * @param {callback} predicate The predicate function to filter rows.
                     * @private
                     */
                    const _filterCampaigns = (selector, predicate) => {
                        $(selector).click(() => {
                            // Clear any existing custom filters before applying a new one
                            $.fn.dataTable.ext.search = [];

                            /**
                             * Custom filter function.
                             *
                             * @param {Object} settings DataTable settings object.
                             * @param {Array} searchData Search data for the row.
                             * @param {int} index Row index.
                             * @param {Object} rowData Row data object.
                             * @return {boolean} True if the row matches the filter, false otherwise.
                             */
                            const filter = (settings, searchData, index, rowData) => {
                                if (!rowData) {
                                    return true;
                                }

                                return predicate(rowData);
                            };

                            $.fn.dataTable.ext.search.push(filter);

                            $('.aa-sovtimer-filter-active').removeClass('aa-sovtimer-filter-active');
                            $(selector).addClass('aa-sovtimer-filter-active');

                            dt.draw();
                        });
                    };

                    // Initial campaign counts update
                    _updateCampaignCounts(dt.rows().data().toArray());

                    // Initialize Bootstrap tooltips
                    _bootstrapTooltip({selector: '.aa-sovtimer'});

                    // Initial cache build
                    _rebuildRowCache();

                    // Initial tick to avoid 1 second delay
                    _tick();

                    // Set interval for ticking every second to update remaining time
                    setInterval(_tick, 1000);

                    // Update the table data every 30 seconds
                    setInterval(() => {
                        fetchGet({url: sovtimerSettings.url.ajaxUpdate})
                            .then((newData) => {
                                dt.clear().rows.add(newData).draw();
                                _updateCampaignCounts(newData);
                                _bootstrapTooltip({selector: '.aa-sovtimer'});
                            })
                            .catch(console.error);
                    }, 30000);

                    // Define filters
                    const _filters = [
                        ['#aa-sovtimer-filter-total-campaigns', () => true],
                        ['#aa-sovtimer-filter-upcoming-campaigns', rowData => rowData.campaign_status === 'upcoming'],
                        ['#aa-sovtimer-filter-active-campaigns', rowData => rowData.campaign_status === 'active']
                    ];

                    _filters.forEach(([selector, predicate]) => _filterCampaigns(selector, predicate));

                    // On DataTable draw, run …
                    dt.on('draw', () => {
                        // Keep cache in sync when table is redrawn or data replaced
                        _rebuildRowCache();

                        // Update campaign counts
                        _updateCampaignCounts(dt.rows().data().toArray());

                        // Re-initialize tooltips
                        _bootstrapTooltip({selector: '.aa-sovtimer'});
                    });
                }
            });
        })
        .catch(console.error);
});
