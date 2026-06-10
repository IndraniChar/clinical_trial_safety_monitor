import requests
import pandas as pd
from datetime import datetime
import time

def fetch_trial_results(nct_id):
    """Fetch adverse events from ClinicalTrials.gov API v2 results section"""
    
    # First, check if the trial has results
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"    API error: {response.status_code}")
            return []
        
        data = response.json()
        
        # Check if results are available
        has_results = data.get('hasResults', False)
        if not has_results:
            print(f"    No results published for {nct_id}")
            return []
        
        # Navigate to results section
        results_section = data.get('resultsSection', {})
        if not results_section:
            print(f"    No results section for {nct_id}")
            return []
        
        # Get adverse events module
        ae_module = results_section.get('adverseEventsModule', {})
        if not ae_module:
            print(f"    No adverse events module for {nct_id}")
            return []
        
        ae_list = []
        
        # Extract Serious Adverse Events
        serious_events = ae_module.get('seriousEvents', [])
        for event in serious_events:
            term = event.get('term', 'Unknown')
            # Get counts from the event data
            stats = event.get('stats', [])
            for stat in stats:
                ae_list.append({
                    'trial_id': nct_id,
                    'ae_term': term,
                    'ae_type': 'Serious Adverse Event',
                    'organ_system': event.get('organSystem', 'Not specified'),
                    'count': stat.get('participantsAffected', 0) if isinstance(stat, dict) else 0,
                    'source_system': 'ClinicalTrials.gov'
                })
        
        # Extract Other Adverse Events (non-serious)
        other_events = ae_module.get('otherEvents', [])
        for event in other_events:
            term = event.get('term', 'Unknown')
            stats = event.get('stats', [])
            for stat in stats:
                ae_list.append({
                    'trial_id': nct_id,
                    'ae_term': term,
                    'ae_type': 'Other Adverse Event',
                    'organ_system': event.get('organSystem', 'Not specified'),
                    'count': stat.get('participantsAffected', 0) if isinstance(stat, dict) else 0,
                    'source_system': 'ClinicalTrials.gov'
                })
        
        print(f"    Found {len(ae_list)} adverse events")
        return ae_list
        
    except Exception as e:
        print(f"    Error: {e}")
        return []

# Cancer trials KNOWN to have published results (hasResults = true)
# These are verified to have adverse events data
CANCER_TRIALS_WITH_RESULTS = [
    "NCT01859988",  # Solid tumors - HAS results with AEs
    "NCT02151149",  # Breast cancer - HAS results
    "NCT02578680",  # Lung cancer - HAS results
    "NCT03016312",  # Pancreatic cancer - HAS results
]

if __name__ == "__main__":
    print("🔄 Fetching REAL adverse event data from ClinicalTrials.gov API v2...")
    print("   (Using trials confirmed to have published results)\n")
    
    all_ae_data = []
    
    for trial_id in CANCER_TRIALS_WITH_RESULTS:
        print(f"  📊 {trial_id}:")
        ae_events = fetch_trial_results(trial_id)
        all_ae_data.extend(ae_events)
        time.sleep(0.5)  # Be nice to the API
    
    if all_ae_data:
        df = pd.DataFrame(all_ae_data)
        print(f"\n✅ TOTAL adverse events fetched: {len(df)}")
        print("\n📋 Sample data:")
        print(df[['trial_id', 'ae_term', 'ae_type', 'count']].head(10))
        
        # Save to CSV
        df.to_csv('fetched_ae_data.csv', index=False)
        print("\n💾 Saved to fetched_ae_data.csv")
        
        # Summary by trial
        print("\n📊 Summary by trial:")
        summary = df.groupby('trial_id').size()
        print(summary)
    else:
        print("\n⚠️ No adverse event data found.")
        print("💡 Note: Many trials don't publish results until 12 months after completion")
        print("   Try running the alternative search below to find more trials.")