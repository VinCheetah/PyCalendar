#!/usr/bin/env python3
"""
Test script to verify pool types are correctly saved and loaded.
"""

import json
from pathlib import Path

def test_pool_types():
    """Check if pool types are present in the latest solution."""
    
    solution_file = Path("solutions/latest_volley.json")
    
    if not solution_file.exists():
        print(f"❌ Solution file not found: {solution_file}")
        return False
    
    print(f"📖 Reading solution from: {solution_file}")
    with open(solution_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check version
    version = data.get('version', 'unknown')
    print(f"   Version: {version}")
    
    # Check if pools have type field
    pools = data.get('entities', {}).get('poules', [])
    print(f"\n📊 Found {len(pools)} pools\n")
    
    pools_with_type = 0
    aller_retour_count = 0
    classique_count = 0
    pools_missing_type = []
    
    # Organize by type
    ar_pools = []
    classique_pools = []
    total_incorrect = 0
    
    for pool in pools:
        pool_id = pool.get('id', 'unknown')
        pool_type = pool.get('type')
        nb_equipes = pool.get('nb_equipes', 0)
        nb_matchs = pool.get('nb_matchs_planifies', 0) + pool.get('nb_matchs_non_planifies', 0)
        
        if pool_type:
            pools_with_type += 1
            if pool_type == 'Aller-Retour':
                aller_retour_count += 1
                # Calculate expected matches for AR pool
                expected = nb_equipes * (nb_equipes - 1)
                status = "✅" if nb_matchs == expected else f"❌ Expected {expected}"
                ar_pools.append((pool_id, nb_equipes, nb_matchs, expected, status))
            else:
                classique_count += 1
                # Calculate expected matches for Classique pool
                expected = nb_equipes * (nb_equipes - 1) // 2
                status = "✅" if nb_matchs == expected else f"❌ Expected {expected}"
                classique_pools.append((pool_id, nb_equipes, nb_matchs, expected, status))
        else:
            pools_missing_type.append(pool_id)
    
    # Display results
    print(f"📈 Pool Type Summary:")
    print(f"   - Pools with type field: {pools_with_type}/{len(pools)}")
    print(f"   - Aller-Retour: {aller_retour_count}")
    print(f"   - Classique: {classique_count}")
    
    if pools_missing_type:
        print(f"\n⚠️  Pools missing type field ({len(pools_missing_type)}):")
        for pool_id in pools_missing_type:
            print(f"   - {pool_id}")
    
    # Display Aller-Retour pools with match counts
    if ar_pools:
        print(f"\n🔄 Aller-Retour Pools ({len(ar_pools)}):")
        print(f"   {'Pool ID':<12} {'Teams':>6} {'Matches':>8} {'Expected':>9} {'Status':<20}")
        print(f"   {'-'*12} {'-'*6} {'-'*8} {'-'*9} {'-'*20}")
        
        incorrect_count = 0
        for pool_id, teams, matches, expected, status in ar_pools:
            print(f"   {pool_id:<12} {teams:>6} {matches:>8} {expected:>9} {status:<20}")
            if "❌" in status:
                incorrect_count += 1
        
        total_incorrect += incorrect_count
        
        if incorrect_count > 0:
            print(f"\n⚠️  {incorrect_count}/{len(ar_pools)} AR pools have incorrect match counts!")
        else:
            print(f"\n✅ All AR pools have correct match counts!")
    
    # Display Classique pools
    if classique_pools:
        print(f"\n📝 Classique Pools ({len(classique_pools)}):")
        print(f"   {'Pool ID':<12} {'Teams':>6} {'Matches':>8} {'Expected':>9} {'Status':<20}")
        print(f"   {'-'*12} {'-'*6} {'-'*8} {'-'*9} {'-'*20}")
        
        incorrect_count = 0
        for pool_id, teams, matches, expected, status in classique_pools:
            print(f"   {pool_id:<12} {teams:>6} {matches:>8} {expected:>9} {status:<20}")
            if "❌" in status:
                incorrect_count += 1
        
        total_incorrect += incorrect_count
        
        if incorrect_count > 0:
            print(f"\n⚠️  {incorrect_count}/{len(classique_pools)} Classique pools have incorrect match counts!")
    
    # Overall result
    print("\n" + "="*70)
    if pools_with_type == len(pools) and total_incorrect == 0:
        print("✅ SUCCESS: All pools have type field and correct match counts!")
        return True
    else:
        print("❌ FAILURE: Some issues detected")
        return False

if __name__ == "__main__":
    success = test_pool_types()
    exit(0 if success else 1)
