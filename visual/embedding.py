import numpy as np
from rdflib import Graph, Namespace, URIRef
from sklearn.metrics.pairwise import cosine_similarity

from pyrdf2vec import RDF2VecTransformer
from pyrdf2vec.walkers import RandomWalker
from pyrdf2vec.embedders import Word2Vec
from pyrdf2vec.graphs import KG
from pyrdf2vec.graphs.vertex import Vertex

"""
=========================================

    Failed Node Embedding Experiment

    Issues:
        Model fails to discover Pokemon given specific attributes & colors

    Potential solution:
        Add more detailed attributes or remove common attributes in the embedding

=========================================

"""

class PokemonRDF2VecModel:
    def __init__(
        self,
        ontology_paths=None,
        kg_paths=None,
        pokemon_namespace="https://pokemonkg.org/instance/pokemon#",
        ontology_namespace="http://example.org/pokemon-ontology#",
        walk_depth=5,
        walks_per_entity=100,
        vector_size=200,
        epochs=10,
    ):
        self.graph = Graph()
        self.pokemon_ns = Namespace(pokemon_namespace)
        self.onto_ns = Namespace(ontology_namespace)

        self.walk_depth = walk_depth
        self.walks_per_entity = walks_per_entity
        self.vector_size = vector_size
        self.epochs = epochs

        self.embeddings = None
        self.entities = None
        self.entity_to_vec = None
        self.w2v = None

        self.kg_path = kg_paths
        self.ontology_path = ontology_paths

        self._load_graph(ontology_paths, kg_paths)

    def _load_graph(self, ontology_paths, kg_paths):
        for path in ontology_paths:
            self.graph.parse(path)
        for path in kg_paths:
            self.graph.parse(path)
        print(f"Triples loaded: {len(self.graph)}")

    def materialize_anatomy(self):
        added = True
        while added:
            added = False
            triples = list(
                self.graph.triples(
                    (None, self.onto_ns.structuralPartOf, None)
                )
            )
            for a, _, b in triples:
                for _, _, c in self.graph.triples(
                    (b, self.onto_ns.structuralPartOf, None)
                ):
                    if (a, self.onto_ns.structuralPartOf, c) not in self.graph:
                        self.graph.add((a, self.onto_ns.structuralPartOf, c))
                        added = True

        print(f"After materialization: {len(self.graph)}")

    def _get_pokemon_entities(self):
        return sorted({
            str(s)
            for s in self.graph.subjects()
            if str(s).startswith(str(self.pokemon_ns))
        })

    def train(self):
        pokemon_entities = self._get_pokemon_entities()
        print(f"Pokémon count: {len(pokemon_entities)}")

        if not pokemon_entities:
            raise RuntimeError("No Pokémon entities found.")

        walker = RandomWalker(
            max_depth=self.walk_depth,
            max_walks=self.walks_per_entity,
            md5_bytes=None,
            with_reverse=True,
        )

        embedder = Word2Vec(
            vector_size=self.vector_size,
            window=5,
            min_count=1,
            epochs=self.epochs,
        )

        rdf2vec = RDF2VecTransformer(
            walkers=[walker],
            embedder=embedder,
        )

        # Build KG using Graph (workaround)
        kg = KG()
        for s, p, o in self.graph:
            subj = Vertex(str(s))

            if isinstance(o, URIRef):
                obj = Vertex(str(o))
            else:
                continue

            pred = Vertex(
                str(p),
                predicate=True,
                vprev=subj,
                vnext=obj
            )

            kg.add_walk(subj, pred, obj)

        self.embeddings, _ = rdf2vec.fit_transform(
            kg, pokemon_entities
        )
        self.entities = pokemon_entities

        self.entity_to_vec = {
            e: self.embeddings[i]
            for i, e in enumerate(self.entities)
        }

        self.w2v = rdf2vec.embedder._model.wv

        print("Training complete.")

    def _node_vec(self, uri):
        return self.w2v[uri] if uri in self.w2v else None

    def build_query_vector(self, attr_weights):
        vecs, weights = [], []

        for attr, w in attr_weights.items():
            if attr in {
                "Purple", "Orange", "Pink", "Blue", "Yellow", 
                "Red", "Green", "Black", "Beige",
            }:
                uri = f"http://dbpedia.org/resource/{attr}"
            else:
                uri = f"{self.onto_ns}{attr}"

            v = self._node_vec(uri)
            if v is not None:
                vecs.append(v * w)
                weights.append(w)

        if not vecs:
            raise ValueError("No valid attributes found in embedding space.")

        return np.sum(vecs, axis=0) / sum(weights)
    
    def predict(self, detected_attributes, top_k=10, verbose=True):
        query_vec = self.build_query_vector(detected_attributes)

        scores = cosine_similarity(
            [query_vec],
            self.embeddings
        )[0]

        ranked = sorted(
            zip(self.entities, scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        if verbose:
            for e, s in ranked:
                print(e.split("#")[-1], round(float(s), 3))

        return ranked