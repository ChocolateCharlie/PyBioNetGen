import xmltodict, copy, os


class BNGGdiff:
    """
    Class to compare two contact maps generated by

    Usage: BNGGdiff(inp1, inp2, out).run()
           BNGGdiff(inp1, inp2, out, mode="matrix").run()

    Arguments
    ---------
    inp1 : str
        path to the first contact map graphml file
    inp2 : str
        path to the second contact map graphml file
    out1 : str
        (optional) path to the output file for inp1 - inp2 graph
    out2 : str
        (optional) path to the second output file for inp2 - inp1 graph
    mode : str
        diff mode, currently available modes are "matrix" and "union"
    """

    def __init__(self, inp1, inp2, out=None, out2=None, mode="matrix") -> None:
        self.input = inp1
        self.input2 = inp2
        iname1 = os.path.basename(inp1).replace(".graphml", "")
        iname2 = os.path.basename(inp2).replace(".graphml", "")
        if out is None:
            out = f"{iname1}_{iname2}_diff.graphml"  # set def
        if out2 is None:
            out2 = f"{iname2}_{iname1}_diff.graphml"  # set def
        self.output = out
        self.output2 = out2
        self.colors = {
            "g1": ["#dadbfd", "#e6e7fe", "#f3f3ff"],
            "g2": ["#ff9e81", "#ffbfaa", "#ffdfd4"],
            "intersect": ["#c4ed9e", "#d9f4be", "#ecf9df"],
        }
        self.available_modes = ["matrix", "union"]
        if mode not in self.available_modes:
            raise RuntimeError(
                f"Mode {mode} is not a valid mode, please choose from {self.available_modes}"
            )
        self.mode = mode

        with open(self.input, "r") as f:
            self.gdict_1 = xmltodict.parse(f.read())
        with open(self.input2, "r") as f:
            self.gdict_2 = xmltodict.parse(f.read())

    def diff_graphs(
        self,
        g1,
        g2,
        colors={
            "g1": ["#dadbfd", "#e6e7fe", "#f3f3ff"],
            "g2": ["#c4ed9e", "#d9f4be", "#ecf9df"],
            "intersect": ["#c4ed9e", "#d9f4be", "#ecf9df"],
        },
    ):
        """
        Given two XML dictionaries (using xmltodict) of two graphml
        graphs, do the diff and return the difference graphml xml in
        dictionary format

        The result is g1-g2. By default g1 only stuff are colored green
        g2 only nodes are colored red and common elements are colored blue.
        These can be changed by the colors kwarg which is a dictionary with
        keys g1, g2 and intersect and colors are given as hexcode strings.

        Usage: diff_graphs(g1_dict, g2_dict)
               diff_graphs(g1_dict, g2_dict,
                    colors={"g1": "#hexstr1",
                            "g2": "#hexstr2",
                            "intersect": "#hexstr3"})

        Arguments
        ---------
        g1 : dict
            input dictionary of the input XML file for the first contact map
        g2 : dict
            second input dictionary of the second input XML file.
        colors (opt): dict
            (optional) A dictionary with keys "g1", "g2" and "intersect". The
            values are color hex strings for the colors you want for graph 1,
            graph 2 and the color for common elements between the two graphs.

        Returns
        -------
        diff : dict
            A dictionary of graphs each of which is a dictionary for the XML file
            of the difference graph. Can be converted back to an XML file using
            `xmltodict` function `unparse`. Each key in the dictionary returned by
            this function is the intended file name for that graph.
        """
        # first do a deepcopy so we don't have to
        # manually do add boilerpate
        if self.mode == "matrix":
            graphs = {}
            diff_gml, _ = self._find_diff(g1, g2, colors=colors)
            graphs[self.output] = diff_gml
            # save recolored g1
            g1_recolor_name = os.path.basename(self.input).replace(
                ".graphml", "_recolored.graphml"
            )
            graphs[g1_recolor_name] = self.gdict_1_recolor
            # save recolored g2
            g2_recolor_name = os.path.basename(self.input2).replace(
                ".graphml", "_recolored.graphml"
            )
            graphs[g2_recolor_name] = self.gdict_2_recolor
            # let's do the reverse
            diff_gml_2, _ = self._find_diff(
                g2,
                g1,
                colors={
                    "g1": colors["g2"],
                    "g2": colors["g1"],
                    "intersect": colors["intersect"],
                },
            )
            graphs[self.output2] = diff_gml_2
            return graphs
        elif self.mode == "union":
            graphs = {}
            g1_name = os.path.basename(self.input).replace(".graphml", "")
            # write recolored g2
            g2_name = os.path.basename(self.input2).replace(".graphml", "")
            union_name = f"{g1_name}_{g2_name}_union.graphml"
            union_gml = self._find_diff_union(g1, g2, colors=colors)
            graphs[union_name] = union_gml
            return graphs
        else:
            raise RuntimeError(
                f"Mode {self.mode} is not a valid mode, please choose from {self.available_modes}"
            )

    def _find_diff_union(
        self,
        g1,
        g2,
        dg=None,
        colors={
            "g1": ["#dadbfd", "#e6e7fe", "#f3f3ff"],
            "g2": ["#c4ed9e", "#d9f4be", "#ecf9df"],
            "intersect": ["#c4ed9e", "#d9f4be", "#ecf9df"],
        },
    ):
        """
        Usage: diff_graphs(g1_dict, g2_dict)
               diff_graphs(g1_dict, g2_dict,
                    colors={"g1": "#hexstr1",
                            "g2": "#hexstr2",
                            "intersect": "#hexstr3"})

        Arguments
        ---------
        g1 : dict
            input dictionary of the input XML file for the first contact map
        g2 : dict
            second input dictionary of the second input XML file.
        dg : dict
            (optional) dictionary to be modified with the difference. If not given it'll
            be a copy of g1 by default.
        colors : dict
            (optional) A dictionary with keys "g1", "g2" and "intersect". The
            values are color hex strings for the colors you want for graph 1,
            graph 2 and the color for common elements between the two graphs.

        Returns
        -------
        diff : dict
            A dictionary for the XML file of the difference graph. Can be converted
            back to an XML file using `xmltodict` function `unparse`.
        """
        # we first want to do the regular diff
        # we'll need to remap g2 names
        dg, rename_map = self._find_diff(g1, g2, dg=dg, colors=colors)

        # now we loop over g2 nodes and add them to dg with the right
        # colors to get the union version
        node_stack = [(["graphml"], [], g2["graphml"])]

        # now we can loop over nodes
        while len(node_stack) > 0:
            dnode = None
            curr_keys, curr_names, curr_node = node_stack.pop(-1)
            # let's take a look at the difference
            dnode = self._get_node_from_names(g1, curr_names)
            if dnode is None and len(curr_names) > 0:
                # this means we don't have this node in diff graph
                # we need to add it in
                dgnode = self._get_node_from_names(dg, curr_names)
                if dgnode is None:
                    curr_dnode = self._add_node_to_graph(
                        curr_node, dg, curr_names, colors=colors, rmap=rename_map
                    )
                else:
                    rename_map[self._get_node_id(curr_node)] = self._get_node_id(dgnode)
            elif dnode is not None and len(curr_names) > 0:
                # we have the same node in g1
                rename_map[self._get_node_id(curr_node)] = self._get_node_id(dnode)
            # if we have graphs in there, add the nodes to the stack
            if "graph" in curr_node.keys():
                # there is a graph in the node, add the nodes to stack
                if isinstance(curr_node["graph"]["node"], list):
                    for inode, node in enumerate(curr_node["graph"]["node"]):
                        ckey = curr_keys + [node["@id"]]
                        node_stack.append(
                            (ckey, curr_names + [self._get_node_name(node)], node)
                        )
                else:
                    ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                    node_stack.append(
                        (
                            ckey,
                            curr_names
                            + [self._get_node_name(curr_node["graph"]["node"])],
                            curr_node["graph"]["node"],
                        )
                    )

        # now we add edges, gotta deal with node renaming
        edge_ctr = len(dg["graphml"]["graph"]["edge"])
        for edge in g2["graphml"]["graph"]["edge"]:
            copied_edge = copy.deepcopy(edge)
            copied_edge["@source"] = rename_map[edge["@source"]]
            copied_edge["@target"] = rename_map[edge["@target"]]
            # ensure we don't already have the same edge
            to_add = True
            for dedge in dg["graphml"]["graph"]["edge"]:
                # exact edge?
                if (dedge["@source"] == copied_edge["@source"]) and (
                    dedge["@target"] == copied_edge["@target"]
                ):
                    to_add = False
                    break
                # inverse direction?
                if (dedge["@target"] == copied_edge["@source"]) and (
                    dedge["@source"] == copied_edge["@target"]
                ):
                    to_add = False
                    break
            if to_add:
                copied_edge["@id"] = f"e{edge_ctr}"
                dg["graphml"]["graph"]["edge"].append(copied_edge)
                edge_ctr += 1

        return dg

    def _find_diff(
        self,
        g1,
        g2,
        dg=None,
        colors={
            "g1": ["#dadbfd", "#e6e7fe", "#f3f3ff"],
            "g2": ["#c4ed9e", "#d9f4be", "#ecf9df"],
            "intersect": ["#c4ed9e", "#d9f4be", "#ecf9df"],
        },
    ):
        if dg is None:
            dg = copy.deepcopy(g1)
        # keep track of naming
        rename_map = {}
        # first find differences in nodes
        # FIXME: Check for single nodes before looping
        node_stack = [(["graphml"], [], g1["graphml"])]
        dnode_stack = [(["graphml"], [], dg["graphml"])]
        while len(node_stack) > 0:
            curr_keys, curr_names, curr_node = node_stack.pop(-1)
            curr_dkeys, curr_dnames, curr_dnode = dnode_stack.pop(-1)
            # write down ID map
            rename_map[self._get_node_id(curr_node)] = self._get_node_id(curr_node)
            # let's take a look at the difference
            g2name = None
            g2node = self._get_node_from_names(g2, curr_names)
            if len(curr_names) > 0:
                # let's get IDs and map them
                curr_name = self._get_node_name(curr_node)
                if not (g2node is None):
                    # also check for name
                    if "data" in g2node.keys():
                        g2name = self._get_node_name(g2node)
                        if g2name is not None or curr_name is not None:
                            if g2name == curr_name:
                                # we have the node in g2, we color it appropriately
                                self._color_node(
                                    curr_dnode,
                                    colors["intersect"][self._get_color_id(curr_dnode)],
                                )
                            else:
                                self._color_node(
                                    curr_dnode,
                                    colors["g1"][self._get_color_id(curr_dnode)],
                                )
                else:
                    if "data" in curr_dnode.keys():
                        # we don't have the node in g2, we color it appropriately
                        self._color_node(
                            curr_dnode, colors["g1"][self._get_color_id(curr_dnode)]
                        )
            # if we have graphs in there, add the nodes to the stack
            if "graph" in curr_node.keys():
                # there is a graph in the node, add the nodes to stack
                if isinstance(curr_node["graph"]["node"], list):
                    for inode, node in enumerate(curr_node["graph"]["node"]):
                        ckey = curr_keys + [node["@id"]]
                        node_stack.append(
                            (ckey, curr_names + [self._get_node_name(node)], node)
                        )
                        dnode = curr_dnode["graph"]["node"][inode]
                        dnode_stack.append(
                            (
                                curr_dkeys + [dnode["@id"]],
                                curr_dnames + [self._get_node_name(dnode)],
                                dnode,
                            )
                        )
                else:
                    ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                    node_stack.append(
                        (
                            ckey,
                            curr_names
                            + [self._get_node_name(curr_node["graph"]["node"])],
                            curr_node["graph"]["node"],
                        )
                    )
                    dnode_stack.append(
                        (
                            ckey,
                            curr_dnames
                            + [self._get_node_name(curr_dnode["graph"]["node"])],
                            curr_dnode["graph"]["node"],
                        )
                    )
        # let's recolor both graphs
        self.gdict_1_recolor = self._recolor_graph(self.gdict_1, self.colors["g1"])
        self.gdict_2_recolor = self._recolor_graph(self.gdict_2, self.colors["g2"])
        # resize all fonts, this adds +20
        self._resize_fonts(self.gdict_1, 20)
        self._resize_fonts(self.gdict_2, 20)
        self._resize_fonts(dg, 20)
        return dg, rename_map

    def _recolor_graph(self, g, color_list):
        recol_g = copy.deepcopy(g)
        node_stack = [(["graphml"], [], recol_g["graphml"])]
        while len(node_stack) > 0:
            curr_keys, curr_names, curr_node = node_stack.pop(-1)
            if len(curr_names) > 0:
                self._color_node(curr_node, color_list[self._get_color_id(curr_node)])
            # if we have graphs in there, add the nodes to the stack
            if "graph" in curr_node.keys():
                # there is a graph in the node, add the nodes to stack
                if isinstance(curr_node["graph"]["node"], list):
                    for inode, node in enumerate(curr_node["graph"]["node"]):
                        ckey = curr_keys + [node["@id"]]
                        node_stack.append(
                            (ckey, curr_names + [self._get_node_name(node)], node)
                        )
                else:
                    ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                    node_stack.append(
                        (
                            ckey,
                            curr_names
                            + [self._get_node_name(curr_node["graph"]["node"])],
                            curr_node["graph"]["node"],
                        )
                    )
        return recol_g

    def _resize_fonts(self, g, add_to_font):
        node_stack = [(["graphml"], [], g["graphml"])]
        while len(node_stack) > 0:
            curr_keys, curr_names, curr_node = node_stack.pop(-1)
            if len(curr_names) > 0:
                self._resize_node_font(curr_node, add_to_font)
            # if we have graphs in there, add the nodes to the stack
            if "graph" in curr_node.keys():
                # there is a graph in the node, add the nodes to stack
                if isinstance(curr_node["graph"]["node"], list):
                    for inode, node in enumerate(curr_node["graph"]["node"]):
                        ckey = curr_keys + [node["@id"]]
                        node_stack.append(
                            (ckey, curr_names + [self._get_node_name(node)], node)
                        )
                else:
                    ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                    node_stack.append(
                        (
                            ckey,
                            curr_names
                            + [self._get_node_name(curr_node["graph"]["node"])],
                            curr_node["graph"]["node"],
                        )
                    )

    def _get_node_from_names(self, g, names):
        if "graphml" in g.keys():
            nodes = g["graphml"]["graph"]["node"]
            if len(names) == 0:
                return g["graphml"]
        else:
            nodes = g["graph"]["node"]
            if len(names) == 0:
                return g
        copy_names = copy.copy(names)
        while len(copy_names) > 0:
            found = False
            key = copy_names.pop(0)
            if isinstance(nodes, list):
                for cnode in nodes:
                    cname = self._get_node_name(cnode)
                    if cname == key:
                        found = True
                        node = cnode
                        if "graph" in node.keys():
                            nodes = node["graph"]["node"]
                    if found:
                        break
            else:
                cname = self._get_node_name(nodes)
                if cname == key:
                    found = True
                    node = nodes
                if "graph" in node.keys():
                    nodes = node["graph"]["node"]
        if not found:
            return None
        return node

    def _get_node_properties(self, node):
        if isinstance(node["data"], list):
            found = False
            for datum in node["data"]:
                if "y:ProxyAutoBoundsNode" in datum.keys():
                    gnode = datum["y:ProxyAutoBoundsNode"]["y:Realizers"]["y:GroupNode"]
                    if isinstance(gnode, list):
                        properties = gnode[0]
                    else:
                        properties = gnode
                    found = True
                elif "y:ShapeNode" in datum.keys():
                    snode = datum["y:ShapeNode"]
                    if isinstance(snode, list):
                        properties = snode[0]
                    else:
                        properties = snode
                    found = True
            if not found:
                raise RuntimeError("Can't find properties for nodes")
        else:
            if "y:ProxyAutoBoundsNode" in node["data"].keys():
                properties = node["data"]["y:ProxyAutoBoundsNode"]["y:Realizers"][
                    "y:GroupNode"
                ]
            elif "y:ShapeNode" in node["data"].keys():
                properties = node["data"]["y:ShapeNode"]
            else:
                raise RuntimeError("Can't find properties for nodes")
        return properties

    def _get_node_name(self, node):
        # node['data'] can be a list if there are
        # multiple data types
        properties = self._get_node_properties(node)
        return properties["y:NodeLabel"]["#text"]

    def _get_node_fill(self, node):
        properties = self._get_node_properties(node)
        return properties["y:Fill"]

    def _get_node_color(self, node):
        return self._get_node_fill(node)["@color"]

    def _resize_node_font(self, node, size):
        properties = self._get_node_properties(node)
        properties["y:NodeLabel"]["@fontSize"] = str(size)

    def _get_font_size(self, node):
        properties = self._get_node_properties(node)
        return int(properties["y:NodeLabel"]["@fontSize"])

    def _get_color_id(self, node):
        # FIXME: This should be fixed at bng level by attaching
        # an attribute to graphml node stating the type of node
        # instead of using colors to check the type
        curr_color = self._get_node_color(node)
        if curr_color == "#D2D2D2":
            # grey indicates a species
            cid = 0
        elif curr_color == "#FFFFFF":
            # white indicates a component
            cid = 1
        elif curr_color == "#FFCC00":
            # yellow indicates a state
            cid = 2
        else:
            raise RuntimeError(f"Node color {curr_color} doesn't match known colors")
        return cid

    def _get_node_from_keylist(self, g, keylist):
        copy_keylist = copy.copy(keylist)
        gkey = copy_keylist.pop(0)
        if len(copy_keylist) == 0:
            # we only have "graphml" as key
            return g[gkey]
        # we are out of group nodes
        if "graph" not in g[gkey].keys():
            return None
        # everything up to here is good,
        # loop over to find the node
        nodes = g[gkey]["graph"]["node"]
        while len(copy_keylist) > 0:
            key = copy_keylist.pop(0)
            found = False
            if isinstance(nodes, list):
                for cnode in nodes:
                    if cnode["@id"] == key:
                        found = True
                        node = cnode
                        try:
                            nodes = node["graph"]["node"]
                        except:
                            break
            else:
                if cnode["@id"] == key:
                    found = True
                    node = cnode
            if not found:
                return None
        return node

    def _color_node(self, node, color) -> bool:
        """
        This uses yEd attributes to change the color of a node

        arguments
            node
            color
        returns
            boolean
        """
        fill = self._get_node_fill(node)
        fill["@color"] = color
        return True

    def _get_node_text(self, node):
        noded = node["data"]["y:ProxyAutoBoundsNode"]["y:Realizers"]
        for key in noded.keys():
            if "y:" in key:
                return noded[key]["y:NodeLabel"]["#text"]
        return None

    def _get_node_id(self, node):
        if "@id" in node:
            return node["@id"]
        else:
            return None

    def _set_node_id(self, node, idstr):
        if "@id" in node:
            node["@id"] = idstr
            return True
        else:
            return False

    def _get_id_list(self, idstr):
        id_str_list = idstr.split("::")
        id_int_list = [int(x[1:]) for x in id_str_list]
        return id_int_list

    def _get_id_str(self, id_list):
        return "::".join([f"n{i}" for i in id_list])

    def _add_node_to_graph(self, node, dg, names, colors=None, rmap={}):
        node_to_add_to = self._get_node_from_names(dg, names[:-1])
        copied_node = copy.deepcopy(node)
        if colors is not None:
            self._color_node(copied_node, colors["g2"][self._get_color_id(copied_node)])
        if "graph" in node_to_add_to.keys():
            if isinstance(node_to_add_to["graph"]["node"], list):
                # first do renaming
                node_ids = [
                    self._get_node_id(node) for node in node_to_add_to["graph"]["node"]
                ]
                node_lists = [self._get_id_list(idstr) for idstr in node_ids]
                new_id = node_lists[-1]
                new_id[-1] += 1
                new_id = self._get_id_str(new_id)
                self._set_node_id(copied_node, new_id)
                # now we can add
                node_to_add_to["graph"]["node"].append(copied_node)
            else:
                # TODO: check if this is done correctly
                # it's a single node and we need to turn
                # it into a list instead
                copied_original_node = copy.deepcopy(node_to_add_to["graph"]["node"])
                og_node_id = self._get_node_id(copied_original_node)
                new_id = self._get_id_list(og_node_id)
                new_id[-1] += 1
                new_id = self._get_id_str(new_id)
                self._set_node_id(copied_node, new_id)
                nodes_to_add = [copied_original_node, copied_node]
                node_to_add_to["graph"]["node"] = nodes_to_add
            # add to rename map
            rmap[self._get_node_id(node)] = self._get_node_id(copied_node)
            # TODO: Need to get in there and rename and recolor each
            # node under the one we just copied
            if "graph" in copied_node:
                # let's rename the graph
                if "@id" in copied_node["graph"]:
                    copied_node["graph"]["@id"] = self._get_node_id(copied_node) + ":"
                node_stack = [([], [], copied_node)]
                while len(node_stack) > 0:
                    curr_keys, curr_names, curr_node = node_stack.pop(-1)
                    # Do stuff here
                    # we need to recolor, re-ID each node and add to rename map
                    if len(curr_names) > 0:
                        parent_node = self._get_node_from_names(
                            copied_node, curr_names[:-1]
                        )
                        if colors is not None:
                            self._color_node(
                                curr_node, colors["g2"][self._get_color_id(curr_node)]
                            )
                        parent_node_id = self._get_node_id(parent_node)
                        new_id = self._get_id_list(parent_node_id)
                        curr_id = self._get_id_list(self._get_node_id(curr_node))
                        new_id += [curr_id[-1]]
                        new_id = self._get_id_str(new_id)
                        self._set_node_id(curr_node, new_id)
                        rmap[self._get_id_str(curr_id)] = new_id
                    # if we have graphs in there, add the nodes to the stack
                    if "graph" in curr_node.keys():
                        # there is a graph in the node, add the nodes to stack
                        if isinstance(curr_node["graph"]["node"], list):
                            for inode, node in enumerate(curr_node["graph"]["node"]):
                                ckey = curr_keys + [node["@id"]]
                                node_stack.append(
                                    (
                                        ckey,
                                        curr_names + [self._get_node_name(node)],
                                        node,
                                    )
                                )
                        else:
                            ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                            node_stack.append(
                                (
                                    ckey,
                                    curr_names
                                    + [self._get_node_name(curr_node["graph"]["node"])],
                                    curr_node["graph"]["node"],
                                )
                            )
        return copied_node

    def run(self) -> dict:
        # Now we have the graphml files, now we do diff
        graphs = self.diff_graphs(self.gdict_1, self.gdict_2, self.colors)
        for graph_name in graphs.keys():
            # now write gml as graphml
            with open(graph_name, "w") as f:
                xmltodict.unparse(graphs[graph_name], output=f)
        return graphs
