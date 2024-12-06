with
source as (
    select * from {{ source('pypi', 'distribution_metadata') }}
),

renamed as (
    select
        metadata_version         as package_metadata_version,
        name                     as package_name,
        version                  as package_version,
        summary                  as package_summary,
        description              as package_description,
        description_content_type as package_description_content_type,
        author                   as package_author,
        author_email             as package_author_email,
        maintainer               as package_maintainer,
        maintainer_email         as package_maintainer_email,
        license                  as package_license,
        keywords                 as package_keywords,
        classifiers              as package_classifiers,
        platform                 as package_platform,
        home_page                as package_home_page,
        download_url             as package_download_url,
        requires_python          as package_requires_python,
        requires                 as package_requires,
        provides                 as package_provides,
        obsoletes                as package_obsoletes,
        requires_dist            as package_requires_dist,
        provides_dist            as package_provides_dist,
        obsoletes_dist           as package_obsoletes_dist,
        requires_external        as package_requires_external,
        project_urls             as package_project_urls,
        uploaded_via             as package_uploaded_via,
        upload_time              as package_uploaded_at,
        filename                 as package_filename,
        size                     as package_size_bytes,
        path                     as package_path,
        python_version           as package_python_version,
        packagetype              as package_package_type,
        comment_text             as package_comment_text,
        has_signature            as package_has_signature,
        md5_digest               as package_md5_digest,
        sha256_digest            as package_sha256_digest,
        blake2_256_digest        as package_blake2_256_digest,
        license_expression       as package_license_expression,
        license_files            as package_license_files
    from
        source
)

select *
from
    renamed
qualify
    row_number() over (
        partition by
            package_name,
            package_version
        order by
            package_uploaded_at desc
    ) = 1
