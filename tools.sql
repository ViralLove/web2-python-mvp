SELECT 
    e.id AS event_id,
    e.name AS event_name,
    e.description AS event_description,
    e.location_type,
    e.location_details,
    e.external_links,
    e.online_access,
    e.created_at AS event_created_at,
    e.updated_at AS event_updated_at,
    o.name AS organizer_name,
    o.description AS organizer_description,
    o.created_at AS organizer_created_at,
    o.updated_at AS organizer_updated_at,
    json_agg(
        json_build_object(
            'start_time', es.start_time,
            'end_time', es.end_time
        )
    ) AS schedules,
    json_agg(
        json_build_object(
            'age_group', da.age_group
        )
    ) AS age_groups,
    json_agg(
        json_build_object(
            'interest', di.interest
        )
    ) AS interests,
    json_agg(
        json_build_object(
            'language', dl.language
        )
    ) AS languages
FROM events e
LEFT JOIN organizers o ON e.organizer_id = o.id
LEFT JOIN event_schedules es ON e.id = es.event_id
LEFT JOIN event_age_groups eag ON e.id = eag.event_id
LEFT JOIN dictionary_age_groups da ON eag.age_group_id = da.id
LEFT JOIN event_interests ei ON e.id = ei.event_id
LEFT JOIN dictionary_interests di ON ei.interest_id = di.id
LEFT JOIN event_languages el ON e.id = el.event_id
LEFT JOIN dictionary_languages dl ON el.language_id = dl.id
--WHERE e.id = $1 -- Подставьте ID события
GROUP BY e.id, o.id;
