import copy
import itertools
from pyzx.graph.base import BaseGraph, VT, ET, EdgeType
from pyzx.graph.graph_s import GraphS

def calculate_lcomp(g: BaseGraph[VT,ET], u: VT):
  vn = list(g.neighbors(u))
  all_edges = set(itertools.combinations(vn,2))
  remove_edges = set([(s,t) for s,t in all_edges if g.connected(s,t) and s in vn and t in vn])
  add_edges= all_edges - remove_edges
  g.remove_edges(remove_edges)
  g.add_edges(add_edges, EdgeType.HADAMARD)

def get_odd_neighbourhood(g: BaseGraph[VT,ET], vertex_set):
  all_neighbors = set()
  for vertex in vertex_set:
    all_neighbors.update(set(g.neighbors(vertex)))
  odd_neighbors = []
  for neighbor in all_neighbors:
    if len(set(g.neighbors(neighbor)).intersection(vertex_set)) % 2 == 1:
      odd_neighbors.append(neighbor)
  return odd_neighbors

def get_all_v_for_lcomp(g, u, gf):
  matches = []
  for candidate in gf:
    if u in get_odd_neighbourhood(g, gf[candidate]):
      matches.append(candidate)
  return matches

def get_odd_neighbourhood_fast(g: BaseGraph[VT,ET], u: VT, gf):
  candidates = []
  u_neighbors = set(g.neighbors(u))
  for key in gf: #TODO: this has runtime O(n²), simplify this to O(n) by reverse lookup dict
    if len(u_neighbors.intersection(gf[key])) % 2 != 0:
      candidates.append(key)
  return candidates

def update_lcomp_gflow(g: BaseGraph[VT,ET], u: VT, gf, set_difference_u=True):
  candidates = get_all_v_for_lcomp(g, u, gf)

  if set_difference_u:
    gf[u].symmetric_difference_update(set([u]))

  for candidate in candidates:
    if candidate != u:
      gf[candidate].symmetric_difference_update(gf[u])
      gf[candidate].symmetric_difference_update(set([u]))

  return gf

def update_gflow_from_double_insertion(gf, vs: VT, ve: VT, vid: VT, vend: VT):
  if ve in gf[vs]:
    gf[vend] = set([ve])
    gf[vid] = set([vend])
    gf[vs].remove(ve)
    gf[vs].update(set([vid]))
  elif vs in gf[ve]:
    gf[vend] = set([vid])
    gf[vid] = set([vs])
    gf[ve].remove(vs)
    gf[ve].update(set([vend]))
  else:
    print("Fatal: unfusion neighbor not in gflow")
    # breakpoint()
  return gf

def update_gflow_from_pivot(g: BaseGraph[VT,ET], u: VT, v: VT, gf):
  g_copy = GraphS()
  g_copy.graph = copy.deepcopy(g.graph)

  update_lcomp_gflow(g_copy, u, gf)
  calculate_lcomp(g_copy, u)
  update_lcomp_gflow(g_copy, v, gf)
  calculate_lcomp(g_copy, v)
  update_lcomp_gflow(g_copy, u, gf, False) #no set difference at last time because u is YZ vertex
  gf_u_yz = gf[u]
  gf_v_yz = gf[v]
  for key in gf:
    if key == u or key == v:
      continue
    if not u in gf[key] and not v in gf[key]:
      continue
    if u in gf[key] and not v in gf[key].symmetric_difference(gf_u_yz):
      gf[key].symmetric_difference_update(gf_u_yz)
    elif v in gf[key] and not u in gf[key].symmetric_difference(gf_v_yz):
      gf[key].symmetric_difference_update(gf_v_yz)
    elif v in gf[key].symmetric_difference(gf_u_yz) and u in gf[key].symmetric_difference(gf_v_yz):
      gf[key].symmetric_difference_update(gf_u_yz)
      gf[key].symmetric_difference_update(gf_v_yz)
    else:
      print("Fatal: no pivot gflow match!")
  
  for key in gf: 
    if u in gf[key] and key != u:
      gf[key].symmetric_difference_update(gf[u])
  gf.pop(u)

  for key in gf: 
    if v in gf[key] and key != v:
      gf[key].symmetric_difference_update(gf[v])
  gf.pop(v)

  return gf #TODO: return not necessary

def update_gflow_from_lcomp(g: BaseGraph[VT,ET], u: VT, gf):
  g_copy = GraphS()
  g_copy.graph = copy.deepcopy(g.graph)
  update_lcomp_gflow(g_copy, u, gf)
  for key in gf: 
    if u in gf[key] and key != u:
      gf[key].symmetric_difference_update(gf[u])
  gf.pop(u) #cleanup, i.e. remove lcomp vertex

  return gf