with
source as (
    select * from {{ source('pypi', 'file_downloads') }}
),

renamed as (
    select
        timestamp    as package_downloaded_at,
        country_code as package_download_country_code,
        url          as package_download_url_path,
        project      as package_name,
        file         as package_download_file_details,
        details      as package_download_details,
        tls_protocol as package_download_tls_protocol,
        tls_cipher   as package_download_tls_cipher
    from
        source
   where 
        {{ pypi_package_filter('project') }}
)

select * from renamed
