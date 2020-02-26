named_config = '''options {
        listen-on port 53 { 0.0.0.0; };
        listen-on-v6 port 53 { ::/0; };
        directory       "/etc/named_conf/";
        dump-file       "/var/bind/data/cache_dump.db";
        statistics-file "/var/bind/data/named_stats.txt";
        memstatistics-file "/var/bind/data/named_mem_stats.txt";
        recursing-file  "/var/bind/data/named.recursing";
        secroots-file   "/var/bind/data/named.secroots";
        allow-query     { 0.0.0.0; ::/0; };


        /* 
         - If you are building an AUTHORITATIVE DNS server, do NOT enable recursion.
         - If you are building a RECURSIVE (caching) DNS server, you need to enable 
           recursion. 
         - If your recursive DNS server has a public IP address, you MUST enable access 
           control to limit queries to your legitimate users. Failing to do so will
           cause your server to become part of large scale DNS amplification 
           attacks. Implementing BCP38 within your network would greatly
           reduce such attack surface 
        */
        recursion yes;

        dnssec-enable yes;
        dnssec-validation yes;

        /* Path to ISC DLV key */
        bindkeys-file "/etc/named.iscdlv.key";

        managed-keys-directory "/var/named/dynamic";

        pid-file "/run/named/named.pid";
        session-keyfile "/run/named/session.key";
};

zone "." IN {
        type hint;
        file "named.ca";
};

{% if isc_config.zones is defined %}
{%for item in isc_config.zones%}
zone {{item.name}} {
    type {{item.type}};
    {% if item.forward is defined %}
    forward only;
    forwarders { {{item.forwarders | join(';')}}; };
    {%endif%}
    {%if item.type == 'master' or item.type == 'hint' or item.type == 'slave'%}
    file "{{item.name}}.db";
    {%endif%}
    {%if item.type == 'slave'%}
    {%if item.allow_notify is defined%}
    allow-notify { {{item.allow_notify | join(';')}}; };
    {%endif%}
    {%if item.max_transfer_ide_out is defined%}
    max-transfer-idle-out {{item.max_transfer_idle_out}};
    {%endif%}
    {%if item.max_transfer_time_in is defined%}
    max-transfer-time-in {{item.max_transfer_time_in}};
    {%endif%}
    {%endif%}
    {%if item.type =='slave' or item.type == 'stub'%}
    {%if item.max_retry_time is defined%}
    max-retry-time {{item.max_retry_time}};
    {%endif%}
    {%if item.min_retry_time is defined%}
    min-retry-time {{item.min_retry_time}};
    {%endif%}
    {%endif%}
    {%if item.alt_transfer_source is defined%}
    alt-transfer-source {{ item.alt_transfer_source }};
    {%endif%}
    {%if item.alt_transfer_source_v6 is defined%}
    alt-transfer-source-v6 {{ item.alt_transfer_source_v6 }};
    {%endif%}
    {%if item.masters is defined%}
    masters { {{item.masters | join(';')}}; };
    {%endif%}
    {%if item.allow_query is defined%}
    allow-query { {{item.allow_query | join(';')}}; };
    {%endif%}
    {%if item.allow_transfer is defined%}
    allow-transfer { {{item.allow_transfer | join(';')}}; };
    {%endif%}
    {%if item.type == 'master'%}
    {%if item.allow_update is defined%}
    allow-update { {{item.allow_update | join(';')}}; };
    {%endif%}
    {%if item.also_notify is defined%}
    also-notify { {{item.also_notify | join(';')}}; };
    {%endif%}
    {%if item.max_transfer_idle_out is defined%}
    max-transfer-idle-out {{item.max_transfer_idle_out}};
    {%endif%}
    {%if item.max_transfer_time_out is defined%}
    max-transfer-time-out {{item.max_transfer_time_out}};
    {%endif%}
    {%endif%}
    {%if item.allow_update_forwarding is defined%}
    allow-update-forwarding { {{item.allow_update_forwarding | join(';')}}; };
    {%endif%}
    {%if item.ixfr_from_differences is defined%}
    ixfr-from-differences {{item.ixfr_from_differences}};
    {%endif%}
    {%if item.max_journal_size is defined%}
    max-journal-size {{item.max_journal_size}};
    {%endif%}
    {%if item.max_refresh_time is defined%}
    max-refresh-time {{item.max_refresh_time}};
    {%endif%}
    {%if item.min_refresh_time is defined%}
    min-refresh-time {{item.min_refresh_time}};
    {%endif%}
    {%if item.zone_statistics is defined%}
    zone-statistics {{item.zone_statistics}};
    {%endif%}
};
{%endfor%}
{%endif%}

include "/etc/named.rfc1912.zones";
include "/etc/named.root.key";'''