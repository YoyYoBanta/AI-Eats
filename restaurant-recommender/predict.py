"""Run a one-off prediction to verify the backend pipeline."""
import logging
from data.startup import initialise
from models.preferences import PreferenceNormalizer
from services.recommender import RecommenderService

logging.basicConfig(level=logging.INFO)

def run_prediction():
    print("Initialising data pipeline (this may take a moment to download the dataset)...")
    repo = initialise()
    
    print("Parsing preferences...")
    # Bellandur, Rating 4.2, Budget 1500 (medium)
    raw_input = {
        "location": "Bellandur",
        "budget": "medium",
        "min_rating": 4.2
    }
    
    # Pass known locations to normalizer
    normalizer = PreferenceNormalizer(repo.get_locations())
    try:
        prefs = normalizer.normalize(raw_input)
    except Exception as e:
        print(f"Error normalizing preferences: {e}")
        return
        
    print(f"Preferences generated: {prefs}")
    
    print("\nStarting recommendation pipeline...")
    recommender = RecommenderService(repo)
    
    try:
        results = recommender.recommend(prefs, top_k=5)
        
        print("\n" + "="*50)
        print("                 RESULTS                 ")
        print("="*50)
        print(f"\nSummary: {results.summary}\n")
        print("Metadata:", results.metadata)
        print("\nRecommendations:")
        for r in results.recommendations:
            print(f"[{r.rank}] {r.restaurant_name} (⭐ {r.rating})")
            print(f"    Cuisines: {', '.join(r.cuisines)}")
            print(f"    Cost for Two: ₹{r.estimated_cost_for_two} ({r.budget_tier})")
            print(f"    Why: {r.explanation}")
            print("-" * 50)
            
    except Exception as e:
        print(f"\nPipeline failed: {e}")

if __name__ == "__main__":
    run_prediction()
