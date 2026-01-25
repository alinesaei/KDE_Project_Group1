from rdflib import Graph, Namespace


class PokemonQueryEngine:
    def __init__(self, ontology_path, entities_path):
        self.graph = Graph()
        self.graph.parse(ontology_path, format="turtle")
        self.graph.parse(entities_path, format="turtle")

        self.EX = Namespace("http://example.org/pokemon-ontology#")
        self.PK = Namespace("https://pokemonkg.org/instance/pokemon#")

    def _color_clause(self, colors):
        if not colors:
            return ""
        values = " ".join(f"dbr:{c}" for c in colors)
        return f"""
        ?pokemon ex:hasColour ?color .
        VALUES ?color {{ {values} }}
        """
    def _attribute_clause(self, attributes):
        if not attributes:
            return ""
        values = " ".join(f"ex:{attr}" for attr in attributes)
        return f"""
        ?pokemon ex:hasAttribute ?part .
        ?part ex:structuralPartOf* ?attribute .
        VALUES ?attribute {{ {values} }}
        """

    def find_with_any(self, attributes, colors):
        attributes_clause = self._attribute_clause(attributes)
        color_clause = self._color_clause(colors)

        query = f"""
        PREFIX ex: <http://example.org/pokemon-ontology#>
        PREFIX pk: <https://pokemonkg.org/instance/pokemon#>
        PREFIX dbr: <http://dbpedia.org/resource/>

        SELECT ?pokemon ?attribute ?color
        WHERE {{
        {color_clause}
        {attributes_clause}
        }}
        """

        results = self.graph.query(query)

        output = {}

        for row in results:
            pokemon = str(row.pokemon).split("#")[-1]

            attribute = (
                str(row.attribute).split("#")[-1]
                if row.attribute else None
            )
            color = (
                str(row.color).split("/")[-1]
                if row.color else None
            )

            if pokemon not in output:
                output[pokemon] = {
                    "attributes": set(),
                    "colors": set(),
                }

            if attribute:
                output[pokemon]["attributes"].add(attribute)

            if color:
                output[pokemon]["colors"].add(color)

        return output


    def find_with_all(self, attributes, colors):
        attribute_clause = self._attribute_clause(attributes)
        color_clause = self._color_clause(colors)

        required_attr_count = len(attributes)
        required_color_count = len(colors)

        having_parts = []
        if attributes:
            having_parts.append(
                f"COUNT(DISTINCT ?attribute) = {required_attr_count}"
            )

        if colors:
            having_parts.append(
                f"COUNT(DISTINCT ?color) = {required_color_count}"
            )

        having_expr = " && ".join(having_parts)

        query = f"""
        PREFIX ex: <http://example.org/pokemon-ontology#>
        PREFIX pk: <https://pokemonkg.org/instance/pokemon#>
        PREFIX dbr: <http://dbpedia.org/resource/>

        SELECT DISTINCT ?pokemon
        WHERE {{
        {attribute_clause}
        {color_clause}
        }}
        GROUP BY ?pokemon
        HAVING ({having_expr})
        """

        results = self.graph.query(query)

        return {
            str(row.pokemon).split("#")[-1]
            for row in results
        }


    def has_attribute(self, pokemon, attribute):
        query = f"""
        PREFIX pk: <https://pokemonkg.org/instance/pokemon#>
        PREFIX ex: <http://example.org/pokemon-ontology#>

        ASK {{
          pk:{pokemon} ex:hasAttribute ?part .
          ?part ex:structuralPartOf* ex:{attribute} .
        }}
        """
        return bool(self.graph.query(query))
    

    def has_color(self, pokemon, color):
        query = f"""
        PREFIX pk: <https://pokemonkg.org/instance/pokemon#>
        PREFIX ex: <http://example.org/pokemon-ontology#>
        PREFIX dbr: <http://dbpedia.org/resource/>

        ASK {{
          pk:{pokemon} ex:hasColour dbr:{color} .
        }}
        """
        return bool(self.graph.query(query))
