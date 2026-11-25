create table clusters (cluster_id number primary key, name varchar2(30), version varchar2(20))
/
create table cl_nodes (node_id number primary key, cluster_id number references clusters, hostname varchar2(30), state varchar2(10))
/
create json relational duality view cluster_dv as
  clusters @insert @update @delete
  { _id : cluster_id, name : name, version : version,
    nodes : cl_nodes @insert @update @delete
      [ { nodeId : node_id, host : hostname, state : state } ] }
/
insert into cluster_dv values ('{"_id":1, "name":"lab-rac", "version":"23.26.4", "nodes":[{"nodeId":11, "host":"rac-alpha", "state":"UP"}, {"nodeId":12, "host":"rac-bravo", "state":"UP"}]}')
/
select cluster_id, name, version from clusters
/
select node_id, cluster_id, hostname, state from cl_nodes order by node_id
/
update cl_nodes set state = 'DOWN' where node_id = 12
/
select json_serialize(json_transform(data, remove '$._metadata') returning varchar2(1000)) doc from cluster_dv
/
update cluster_dv d set data = json_transform(data, set '$.nodes[1].state' = 'UP', set '$.name' = 'lab-rac-prod') where d.data."_id" = 1
/
select c.name, n.hostname, n.state from clusters c join cl_nodes n on n.cluster_id = c.cluster_id order by n.node_id
/
select json_value(data, '$._metadata.etag') etag from cluster_dv
/
