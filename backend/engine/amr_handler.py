import amrlib
import os
from engine.graph_manipulator import GraphManipulator

class AMRHandler:
    def __init__(self):
        # Note: Models will be downloaded/loaded in the Colab environment
        self.parser = None
        self.generator = None
        self.manipulator = GraphManipulator()

    def _initialize_models(self):
        """Lazy loading of models to save memory initially."""
        if not self.parser:
            try:
                # Check for manually downloaded models in the 'models' directory
                stog_path = "models/model_stog"
                gtos_path = "models/model_gtos"
                
                if os.path.exists(stog_path):
                    self.parser = amrlib.load_stog_model(model_dir=stog_path)
                else:
                    self.parser = amrlib.load_stog_model()
                    
                if os.path.exists(gtos_path):
                    self.generator = gtos_model = amrlib.load_gtos_model(model_dir=gtos_path)
                else:
                    self.generator = amrlib.load_gtos_model()
            except Exception as e:
                print(f"Error loading AMR models: {e}")
                # Fallback or placeholder for local development without models
                pass

    def text_to_graphs(self, text):
        self._initialize_models()
        if not self.parser:
            return ["(a / amr-placeholder :content \"model not loaded\")"]
        
        # Split text into sentences if necessary, amrlib parser handles lists
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        graphs = self.parser.parse_sents(sentences)
        return graphs

    def graphs_to_text(self, graphs):
        self._initialize_models()
        if not self.generator:
            return "Generation placeholder: Model not loaded."
        
        sents, _ = self.generator.generate(graphs)
        return " ".join(sents)

    def humanize_via_amr(self, text):
        """Basic AMR round-trip to strip syntactic DNA."""
        graphs = self.text_to_graphs(text)
        # Phase 2, Step 2: Apply Graph Burstiness
        manipulated_graphs = self.manipulator.apply_burstiness(graphs)
        humanized_text = self.graphs_to_text(manipulated_graphs)
        return humanized_text
