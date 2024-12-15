/* global sovtimerJsSettingsDefaults, sovtimerJsSettingsOverride, moment */

$(document).ready(() => {
    'use strict';

    /**
     * Checks if the given item is a plain object, excluding arrays and dates.
     *
     * @param {*} item - The item to check.
     * @returns {boolean} True if the item is a plain object, false otherwise.
     */
    function isObject (item) {
        return (
            item && typeof item === 'object' && !Array.isArray(item) && !(item instanceof Date)
        );
    }

    /**
     * Recursively merges properties from source objects into a target object. If a property at the current level is an object,
     * and both target and source have it, the property is merged. Otherwise, the source property overwrites the target property.
     * This function does not modify the source objects and prevents prototype pollution by not allowing __proto__, constructor,
     * and prototype property names.
     *
     * @param {Object} target - The target object to merge properties into.
     * @param {...Object} sources - One or more source objects from which to merge properties.
     * @returns {Object} The target object after merging properties from sources.
     */
    function deepMerge (target, ...sources) {
        if (!sources.length) {
            return target;
        }

        // Iterate through each source object without modifying the `sources` array.
        sources.forEach(source => {
            if (isObject(target) && isObject(source)) {
                for (const key in source) {
                    if (isObject(source[key])) {
                        if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
                            continue; // Skip potentially dangerous keys to prevent prototype pollution.
                        }

                        if (!target[key] || !isObject(target[key])) {
                            target[key] = {};
                        }

                        deepMerge(target[key], source[key]);
                    } else {
                        target[key] = source[key];
                    }
                }
            }
        });

        return target;
    }

    // Build the settings object
    let sovtimerSettings = sovtimerJsSettingsDefaults;
    if (typeof sovtimerJsSettingsOverride !== 'undefined') {
        sovtimerSettings = deepMerge(
            sovtimerJsSettingsDefaults,
            sovtimerJsSettingsOverride
        );
    }

    const elementTimerTotal = $('.aa-sovtimer-timers-total');
    const elementTimerUpcoming = $('.aa-sovtimer-timers-upcoming');
    const elementTimerActive = $('.aa-sovtimer-timers-active');

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
    const sovCampaignTable = $('.aa-sovtimer-campaigns').DataTable({
        language: sovtimerSettings.dataTables.translation,
        ajax: {
            url: sovtimerSettings.url.ajaxUpdate,
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
                render: (data) => {
                    return moment(data).utc().format(sovtimerSettings.dateformat);
                }
            },
            {
                data: 'remaining_time'
            },
            {
                data: 'campaign_progress'
            },

            // Hidden columns
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
            // {
            //     width: '115px',
            //     targets: [7]
            // },
            // {
            //     width: '150px',
            //     targets: [8]
            // }
        ],
        order: [[6, 'asc']],
        filterDropDown: {
            columns: [
                {
                    idx: 0,
                    title: sovtimerSettings.translations.type
                },
                {
                    idx: 10,
                    title: sovtimerSettings.translations.system
                },
                {
                    idx: 11,
                    title: sovtimerSettings.translations.constellation
                },
                {
                    idx: 12,
                    title: sovtimerSettings.translations.region
                },
                {
                    idx: 13,
                    title: sovtimerSettings.translations.owner
                },
                {
                    idx: 14,
                    title: sovtimerSettings.translations.activeCampaign
                }
            ],
            autoSize: false,
            bootstrap: true,
            bootstrap_version: 5,
        },
        createdRow: (row, data) => {
            // Total timer
            const currentTotal = elementTimerTotal.html();
            const newTotal = parseInt(currentTotal) + 1;

            elementTimerTotal.html(newTotal);

            // Upcoming timer (< 4 hrs)
            if (data.active_campaign === sovtimerSettings.translations.no && data.remaining_time_in_seconds <= 14400) {
                $(row).addClass('aa-sovtimer-upcoming-campaign');

                const currentUpcoming = elementTimerUpcoming.html();
                const newUpcoming = parseInt(currentUpcoming) + 1;

                elementTimerUpcoming.html(newUpcoming);
            }

            // Active timer
            if (data.active_campaign === sovtimerSettings.translations.yes) {
                $(row).addClass('aa-sovtimer-active-campaign');

                const currentActive = elementTimerActive.html();
                const newActive = parseInt(currentActive) + 1;

                elementTimerActive.html(newActive);
            }
        },
        paging: false
    });

    /**
     * Update the datatable information every 30 seconds
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
                if (item.active_campaign === sovtimerSettings.translations.no && item.remaining_time_in_seconds <= 14400) {
                    const currentUpcoming = elementTimerUpcoming.html();
                    const newUpcoming = parseInt(currentUpcoming) + 1;

                    elementTimerUpcoming.html(newUpcoming);
                }

                // Active timer
                if (item.active_campaign === sovtimerSettings.translations.yes) {
                    const currentActive = elementTimerActive.html();
                    const newActive = parseInt(currentActive) + 1;

                    elementTimerActive.html(newActive);
                }
            });
        });
    }, 30000);

    /**
     * Update the remaining time every second
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
