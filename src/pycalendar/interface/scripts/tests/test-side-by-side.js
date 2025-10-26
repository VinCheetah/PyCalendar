/**
 * Tests pour le système d'affichage côte à côte
 * Vérification des modules SlotManager et MatchCardRenderer
 */

// Test 1: SlotManager - Organisation des matchs

const slotManager = new SlotManager();

// Test avec 1 match
const test1Matches = [{ match_id: 1, equipe1_nom: 'LYON 1 (1)', equipe2_nom: 'LYON 2 (1)' }];
const result1 = slotManager.organizeSlotMatches(test1Matches, 2);

// Test avec 2 matchs
const test2Matches = [
    { match_id: 1, equipe1_nom: 'LYON 1 (1)', equipe2_nom: 'LYON 2 (1)' },
    { match_id: 2, equipe1_nom: 'LYON 3 (1)', equipe2_nom: 'INSA (1)' }
];
const result2 = slotManager.organizeSlotMatches(test2Matches, 2);

// Test avec 3 matchs (dépassement de capacité)
const test3Matches = [
    { match_id: 1, equipe1_nom: 'LYON 1 (1)', equipe2_nom: 'LYON 2 (1)' },
    { match_id: 2, equipe1_nom: 'LYON 3 (1)', equipe2_nom: 'INSA (1)' },
    { match_id: 3, equipe1_nom: 'ECL (1)', equipe2_nom: 'ENS (1)' }
];
const result3 = slotManager.organizeSlotMatches(test3Matches, 2);


// Test 2: Détection des conflits

// Conflit de capacité
const conflictMatches = [
    { match_id: 1, equipe1_id: 'E1', equipe2_id: 'E2', equipe1_institution: 'LYON 1', equipe2_institution: 'LYON 2' },
    { match_id: 2, equipe1_id: 'E3', equipe2_id: 'E4', equipe1_institution: 'INSA', equipe2_institution: 'ECL' },
    { match_id: 3, equipe1_id: 'E5', equipe2_id: 'E6', equipe1_institution: 'ENS', equipe2_institution: 'ENTPE' }
];
const conflicts1 = slotManager.detectConflicts(conflictMatches, 2);

// Conflit d'équipe en double
const duplicateMatches = [
    { match_id: 1, equipe1_id: 'E1', equipe2_id: 'E2', equipe1_nom: 'LYON 1 (1)', equipe2_nom: 'LYON 2 (1)' },
    { match_id: 2, equipe1_id: 'E1', equipe2_id: 'E3', equipe1_nom: 'LYON 1 (1)', equipe2_nom: 'INSA (1)' }  // E1 en double!
];
const conflicts2 = slotManager.detectConflicts(duplicateMatches, 3);


// Test 3: MatchCardRenderer

const renderer = new MatchCardRenderer();

// Test du mode compact

// Test des classes de pénalités

// Test du raccourcissement des noms
const shortName = renderer.shortenName('LYON 1 (5)');


// Test 4: Calcul de hauteur de slot



// Test 5: Statistiques de slot

const statsMatches = [
    { 
        match_id: 1, 
        is_fixed: true, 
        is_external: false, 
        is_entente: true,
        penalties: { total: 25 }
    },
    { 
        match_id: 2, 
        is_fixed: false, 
        is_external: true, 
        is_entente: false,
        penalties: { total: 50 }
    }
];

const stats = slotManager.getSlotStats(statsMatches);


// Résumé final
