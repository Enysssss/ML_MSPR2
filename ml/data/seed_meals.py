"""
Seed script — crée la table meals et insère ~150 repas complets.
Repas construits selon les guidelines ACSM 2022 / OMS par profil fitness.
Allergènes : gluten, lactose, oeufs, fruits_a_coque, arachides, soja, poisson, crustaces
"""

import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ["DATABASE_URL"]

MEALS = [
    {"name": "Omelette 4 œufs, avocat et pain complet", "meal_type": "breakfast", "calories": 680, "proteins_g": 38, "carbs_g": 42, "fats_g": 32, "allergens": ["oeufs", "gluten"], "profiles": ["prise_masse_confirme", "prise_masse_debutant"]},
    {"name": "Porridge avoine, whey vanille et banane", "meal_type": "breakfast", "calories": 520, "proteins_g": 35, "carbs_g": 68, "fats_g": 8, "allergens": ["gluten", "lactose"], "profiles": ["prise_masse_debutant", "prise_masse_confirme"]},
    {"name": "Pancakes protéinés au fromage blanc", "meal_type": "breakfast", "calories": 490, "proteins_g": 32, "carbs_g": 52, "fats_g": 12, "allergens": ["gluten", "lactose", "oeufs"], "profiles": ["prise_masse_debutant"]},
    {"name": "Bagel saumon fumé, cream cheese et câpres", "meal_type": "breakfast", "calories": 540, "proteins_g": 30, "carbs_g": 55, "fats_g": 18, "allergens": ["gluten", "lactose", "poisson"], "profiles": ["prise_masse_confirme", "amelioration_cardio"]},
    {"name": "Bowl de quinoa, œufs pochés et épinards", "meal_type": "breakfast", "calories": 460, "proteins_g": 28, "carbs_g": 48, "fats_g": 14, "allergens": ["oeufs"], "profiles": ["prise_masse_debutant", "maintien_bien_etre"]},
    {"name": "Smoothie bowl açaï, granola et fruits rouges", "meal_type": "breakfast", "calories": 420, "proteins_g": 12, "carbs_g": 72, "fats_g": 10, "allergens": ["gluten", "fruits_a_coque"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},
    {"name": "Yaourt grec 0%, graines de chia et framboises", "meal_type": "breakfast", "calories": 220, "proteins_g": 18, "carbs_g": 22, "fats_g": 4, "allergens": ["lactose"], "profiles": ["perte_poids_debutant", "perte_poids_confirme"]},
    {"name": "Blanc d'œuf brouillé, tomates et herbes", "meal_type": "breakfast", "calories": 180, "proteins_g": 20, "carbs_g": 8, "fats_g": 5, "allergens": ["oeufs"], "profiles": ["perte_poids_confirme", "perte_poids_debutant"]},
    {"name": "Tartine de seigle, avocat et œuf poché", "meal_type": "breakfast", "calories": 310, "proteins_g": 14, "carbs_g": 30, "fats_g": 16, "allergens": ["gluten", "oeufs"], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
    {"name": "Smoothie vert épinards, pomme, concombre", "meal_type": "breakfast", "calories": 160, "proteins_g": 4, "carbs_g": 32, "fats_g": 2, "allergens": [], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
    {"name": "Fromage blanc 0%, compote pomme cannelle", "meal_type": "breakfast", "calories": 190, "proteins_g": 15, "carbs_g": 28, "fats_g": 1, "allergens": ["lactose"], "profiles": ["perte_poids_debutant"]},
    {"name": "Muesli aux fruits secs et lait d'amande", "meal_type": "breakfast", "calories": 380, "proteins_g": 10, "carbs_g": 62, "fats_g": 10, "allergens": ["gluten", "fruits_a_coque"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},
    {"name": "Tartine pain de campagne, beurre de cacahuète et banane", "meal_type": "breakfast", "calories": 400, "proteins_g": 12, "carbs_g": 58, "fats_g": 14, "allergens": ["gluten", "arachides"], "profiles": ["amelioration_cardio"]},
    {"name": "Œufs brouillés, champignons sautés et pain grillé", "meal_type": "breakfast", "calories": 350, "proteins_g": 22, "carbs_g": 30, "fats_g": 14, "allergens": ["oeufs", "gluten"], "profiles": ["maintien_bien_etre"]},
    {"name": "Porridge avoine, lait de coco et mangue", "meal_type": "breakfast", "calories": 360, "proteins_g": 8, "carbs_g": 60, "fats_g": 10, "allergens": ["gluten"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},

    {"name": "Poulet grillé 200g, riz basmati et brocoli", "meal_type": "lunch", "calories": 620, "proteins_g": 52, "carbs_g": 68, "fats_g": 10, "allergens": [], "profiles": ["prise_masse_confirme", "prise_masse_debutant"]},
    {"name": "Steak haché 180g, pâtes complètes et sauce tomate", "meal_type": "lunch", "calories": 700, "proteins_g": 48, "carbs_g": 72, "fats_g": 20, "allergens": ["gluten"], "profiles": ["prise_masse_confirme"]},
    {"name": "Thon en boîte, lentilles vertes et carottes rôties", "meal_type": "lunch", "calories": 520, "proteins_g": 42, "carbs_g": 48, "fats_g": 10, "allergens": ["poisson"], "profiles": ["prise_masse_debutant", "prise_masse_confirme"]},
    {"name": "Saumon 180g, patate douce et haricots verts", "meal_type": "lunch", "calories": 590, "proteins_g": 44, "carbs_g": 44, "fats_g": 18, "allergens": ["poisson"], "profiles": ["prise_masse_confirme", "amelioration_cardio"]},
    {"name": "Bowl poulet teriyaki, riz japonica et edamame", "meal_type": "lunch", "calories": 650, "proteins_g": 46, "carbs_g": 74, "fats_g": 12, "allergens": ["soja", "gluten"], "profiles": ["prise_masse_confirme"]},
    {"name": "Wrap dinde, avocat, salade et tortilla complète", "meal_type": "lunch", "calories": 540, "proteins_g": 36, "carbs_g": 48, "fats_g": 18, "allergens": ["gluten"], "profiles": ["prise_masse_debutant", "maintien_bien_etre"]},
    {"name": "Pâtes al dente, bœuf haché et parmesan", "meal_type": "lunch", "calories": 720, "proteins_g": 45, "carbs_g": 80, "fats_g": 22, "allergens": ["gluten", "lactose"], "profiles": ["prise_masse_confirme"]},
    {"name": "Riz complet, tofu grillé et légumes sautés", "meal_type": "lunch", "calories": 490, "proteins_g": 26, "carbs_g": 68, "fats_g": 12, "allergens": ["soja", "gluten"], "profiles": ["prise_masse_debutant", "maintien_bien_etre"]},
    {"name": "Salade de poulet grillé, quinoa et légumes croquants", "meal_type": "lunch", "calories": 380, "proteins_g": 34, "carbs_g": 30, "fats_g": 10, "allergens": [], "profiles": ["perte_poids_confirme", "perte_poids_debutant"]},
    {"name": "Soupe de lentilles corail et épices", "meal_type": "lunch", "calories": 290, "proteins_g": 18, "carbs_g": 40, "fats_g": 5, "allergens": [], "profiles": ["perte_poids_debutant"]},
    {"name": "Filet de cabillaud vapeur, courgettes et citron", "meal_type": "lunch", "calories": 280, "proteins_g": 34, "carbs_g": 10, "fats_g": 8, "allergens": ["poisson"], "profiles": ["perte_poids_confirme", "perte_poids_debutant"]},
    {"name": "Salade niçoise légère (thon, haricots, tomate)", "meal_type": "lunch", "calories": 320, "proteins_g": 28, "carbs_g": 18, "fats_g": 12, "allergens": ["poisson", "oeufs"], "profiles": ["perte_poids_confirme"]},
    {"name": "Soupe de légumes et blanc de poulet effiloché", "meal_type": "lunch", "calories": 250, "proteins_g": 26, "carbs_g": 22, "fats_g": 5, "allergens": [], "profiles": ["perte_poids_debutant"]},
    {"name": "Bowl Buddha : pois chiches, légumes rôtis, tahini", "meal_type": "lunch", "calories": 420, "proteins_g": 16, "carbs_g": 52, "fats_g": 16, "allergens": ["fruits_a_coque"], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
    {"name": "Crevettes sautées, nouilles de courgette et pesto", "meal_type": "lunch", "calories": 300, "proteins_g": 28, "carbs_g": 14, "fats_g": 14, "allergens": ["crustaces", "fruits_a_coque"], "profiles": ["perte_poids_confirme"]},
    {"name": "Pâtes complètes, sauce pesto et poulet", "meal_type": "lunch", "calories": 560, "proteins_g": 36, "carbs_g": 64, "fats_g": 14, "allergens": ["gluten", "fruits_a_coque", "lactose"], "profiles": ["amelioration_cardio"]},
    {"name": "Riz basmati, dahl de lentilles et naan", "meal_type": "lunch", "calories": 520, "proteins_g": 20, "carbs_g": 82, "fats_g": 10, "allergens": ["gluten"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},
    {"name": "Quiche légumes du soleil (courgette, poivron)", "meal_type": "lunch", "calories": 380, "proteins_g": 16, "carbs_g": 28, "fats_g": 22, "allergens": ["gluten", "lactose", "oeufs"], "profiles": ["maintien_bien_etre"]},
    {"name": "Taboulé libanais, falafel et houmous", "meal_type": "lunch", "calories": 460, "proteins_g": 16, "carbs_g": 60, "fats_g": 16, "allergens": ["gluten", "fruits_a_coque"], "profiles": ["maintien_bien_etre", "amelioration_cardio"]},
    {"name": "Sushis assortis (8 pièces) et salade de chou", "meal_type": "lunch", "calories": 420, "proteins_g": 18, "carbs_g": 62, "fats_g": 10, "allergens": ["poisson", "gluten", "soja"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},
    {"name": "Sandwich poulet-avocat sur pain de seigle", "meal_type": "lunch", "calories": 480, "proteins_g": 30, "carbs_g": 44, "fats_g": 18, "allergens": ["gluten"], "profiles": ["maintien_bien_etre"]},

    {"name": "Côte de bœuf 250g, purée patate douce et asperges", "meal_type": "dinner", "calories": 780, "proteins_g": 58, "carbs_g": 42, "fats_g": 36, "allergens": [], "profiles": ["prise_masse_confirme"]},
    {"name": "Filet de poulet farci fromage, jambon et riz", "meal_type": "dinner", "calories": 650, "proteins_g": 54, "carbs_g": 48, "fats_g": 20, "allergens": ["lactose"], "profiles": ["prise_masse_confirme", "prise_masse_debutant"]},
    {"name": "Pâtes bolognaise bœuf/porc, parmesan râpé", "meal_type": "dinner", "calories": 720, "proteins_g": 46, "carbs_g": 76, "fats_g": 22, "allergens": ["gluten", "lactose"], "profiles": ["prise_masse_confirme"]},
    {"name": "Lasagnes bœuf maison, béchamel légère", "meal_type": "dinner", "calories": 680, "proteins_g": 38, "carbs_g": 62, "fats_g": 28, "allergens": ["gluten", "lactose", "oeufs"], "profiles": ["prise_masse_confirme", "prise_masse_debutant"]},
    {"name": "Saumon en croûte d'herbes, quinoa et épinards", "meal_type": "dinner", "calories": 620, "proteins_g": 48, "carbs_g": 40, "fats_g": 24, "allergens": ["poisson", "gluten"], "profiles": ["prise_masse_confirme"]},
    {"name": "Escalope de dinde, gnocchis et sauce crème champignon", "meal_type": "dinner", "calories": 590, "proteins_g": 42, "carbs_g": 56, "fats_g": 18, "allergens": ["gluten", "lactose", "oeufs"], "profiles": ["prise_masse_debutant"]},
    {"name": "Curry de poulet au lait de coco et riz thaï", "meal_type": "dinner", "calories": 620, "proteins_g": 40, "carbs_g": 64, "fats_g": 20, "allergens": [], "profiles": ["prise_masse_debutant", "maintien_bien_etre"]},
    {"name": "Pavé de saumon grillé, ratatouille et quinoa", "meal_type": "dinner", "calories": 420, "proteins_g": 38, "carbs_g": 32, "fats_g": 14, "allergens": ["poisson"], "profiles": ["perte_poids_confirme", "perte_poids_debutant"]},
    {"name": "Blanc de poulet vapeur, haricots verts et tomates", "meal_type": "dinner", "calories": 290, "proteins_g": 36, "carbs_g": 16, "fats_g": 6, "allergens": [], "profiles": ["perte_poids_debutant", "perte_poids_confirme"]},
    {"name": "Cabillaud en papillote, fenouil et citron", "meal_type": "dinner", "calories": 260, "proteins_g": 32, "carbs_g": 10, "fats_g": 8, "allergens": ["poisson"], "profiles": ["perte_poids_confirme"]},
    {"name": "Soupe miso, tofu et wakamé", "meal_type": "dinner", "calories": 220, "proteins_g": 16, "carbs_g": 18, "fats_g": 8, "allergens": ["soja", "poisson"], "profiles": ["perte_poids_debutant", "perte_poids_confirme"]},
    {"name": "Wok de légumes et crevettes, sauce soja légère", "meal_type": "dinner", "calories": 310, "proteins_g": 28, "carbs_g": 24, "fats_g": 8, "allergens": ["crustaces", "soja", "gluten"], "profiles": ["perte_poids_confirme"]},
    {"name": "Omelette aux légumes du frigo et salade verte", "meal_type": "dinner", "calories": 280, "proteins_g": 22, "carbs_g": 10, "fats_g": 16, "allergens": ["oeufs"], "profiles": ["perte_poids_debutant"]},
    {"name": "Velouté de butternut, noix de muscade et fromage blanc", "meal_type": "dinner", "calories": 240, "proteins_g": 10, "carbs_g": 32, "fats_g": 8, "allergens": ["lactose"], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
    {"name": "Pizza maison pâte fine, mozzarella et légumes", "meal_type": "dinner", "calories": 520, "proteins_g": 22, "carbs_g": 68, "fats_g": 16, "allergens": ["gluten", "lactose"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},
    {"name": "Risotto champignons et parmesan", "meal_type": "dinner", "calories": 500, "proteins_g": 16, "carbs_g": 72, "fats_g": 14, "allergens": ["lactose"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},
    {"name": "Tajine de poulet aux olives et citron confit", "meal_type": "dinner", "calories": 460, "proteins_g": 34, "carbs_g": 28, "fats_g": 20, "allergens": [], "profiles": ["maintien_bien_etre", "amelioration_cardio"]},
    {"name": "Gratin de légumes et mozzarella", "meal_type": "dinner", "calories": 380, "proteins_g": 18, "carbs_g": 32, "fats_g": 18, "allergens": ["lactose"], "profiles": ["maintien_bien_etre"]},
    {"name": "Pad thaï crevettes, nouilles de riz et cacahuètes", "meal_type": "dinner", "calories": 540, "proteins_g": 28, "carbs_g": 66, "fats_g": 16, "allergens": ["crustaces", "arachides", "soja", "gluten", "oeufs"], "profiles": ["amelioration_cardio"]},
    {"name": "Burger maison pain complet, steak, légumes grillés", "meal_type": "dinner", "calories": 580, "proteins_g": 38, "carbs_g": 52, "fats_g": 22, "allergens": ["gluten", "oeufs", "lactose"], "profiles": ["maintien_bien_etre", "prise_masse_debutant"]},
    {"name": "Moules marinières, frites de patate douce", "meal_type": "dinner", "calories": 480, "proteins_g": 30, "carbs_g": 44, "fats_g": 18, "allergens": ["crustaces", "lactose", "gluten"], "profiles": ["maintien_bien_etre", "amelioration_cardio"]},

    {"name": "Shake protéiné whey chocolat et lait demi-écrémé", "meal_type": "snack", "calories": 320, "proteins_g": 38, "carbs_g": 28, "fats_g": 6, "allergens": ["lactose"], "profiles": ["prise_masse_confirme", "prise_masse_debutant"]},
    {"name": "Pain de riz, beurre de cacahuète et miel", "meal_type": "snack", "calories": 280, "proteins_g": 10, "carbs_g": 38, "fats_g": 10, "allergens": ["arachides"], "profiles": ["prise_masse_debutant", "prise_masse_confirme", "amelioration_cardio"]},
    {"name": "Fromage blanc 20%, noix et fruits rouges", "meal_type": "snack", "calories": 240, "proteins_g": 16, "carbs_g": 18, "fats_g": 12, "allergens": ["lactose", "fruits_a_coque"], "profiles": ["prise_masse_debutant", "maintien_bien_etre"]},
    {"name": "Galette de riz, amandes effilées et raisins secs", "meal_type": "snack", "calories": 220, "proteins_g": 6, "carbs_g": 36, "fats_g": 8, "allergens": ["fruits_a_coque"], "profiles": ["amelioration_cardio", "prise_masse_debutant"]},
    {"name": "Mix trail : amandes, noix de cajou, cranberries", "meal_type": "snack", "calories": 300, "proteins_g": 8, "carbs_g": 28, "fats_g": 18, "allergens": ["fruits_a_coque"], "profiles": ["prise_masse_confirme", "amelioration_cardio"]},
    {"name": "Œufs durs (2) et bâtonnets de légumes", "meal_type": "snack", "calories": 180, "proteins_g": 14, "carbs_g": 6, "fats_g": 10, "allergens": ["oeufs"], "profiles": ["prise_masse_debutant", "perte_poids_confirme"]},
    {"name": "Concombre, houmous et carottes bâtonnets", "meal_type": "snack", "calories": 140, "proteins_g": 6, "carbs_g": 16, "fats_g": 6, "allergens": ["fruits_a_coque"], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
    {"name": "Yaourt grec 0% et 1 fruit de saison", "meal_type": "snack", "calories": 130, "proteins_g": 12, "carbs_g": 18, "fats_g": 0, "allergens": ["lactose"], "profiles": ["perte_poids_debutant", "perte_poids_confirme"]},
    {"name": "Edamame salé (100g)", "meal_type": "snack", "calories": 120, "proteins_g": 12, "carbs_g": 8, "fats_g": 5, "allergens": ["soja"], "profiles": ["perte_poids_confirme", "perte_poids_debutant"]},
    {"name": "Blanc de dinde (2 tranches) et cornichons", "meal_type": "snack", "calories": 100, "proteins_g": 16, "carbs_g": 2, "fats_g": 2, "allergens": [], "profiles": ["perte_poids_confirme"]},
    {"name": "Smoothie protéiné : épinards, banane, lait d'amande", "meal_type": "snack", "calories": 190, "proteins_g": 10, "carbs_g": 28, "fats_g": 5, "allergens": ["fruits_a_coque"], "profiles": ["perte_poids_debutant", "amelioration_cardio"]},
    {"name": "Barre énergétique avoine-miel maison", "meal_type": "snack", "calories": 220, "proteins_g": 6, "carbs_g": 42, "fats_g": 5, "allergens": ["gluten", "fruits_a_coque"], "profiles": ["amelioration_cardio"]},
    {"name": "Banane et 20g de noix de cajou", "meal_type": "snack", "calories": 210, "proteins_g": 5, "carbs_g": 34, "fats_g": 8, "allergens": ["fruits_a_coque"], "profiles": ["amelioration_cardio", "maintien_bien_etre"]},
    {"name": "Fromage blanc à la fraise et graines de lin", "meal_type": "snack", "calories": 160, "proteins_g": 12, "carbs_g": 18, "fats_g": 4, "allergens": ["lactose"], "profiles": ["maintien_bien_etre"]},
    {"name": "Crackers de seigle et tzatziki", "meal_type": "snack", "calories": 190, "proteins_g": 6, "carbs_g": 26, "fats_g": 7, "allergens": ["gluten", "lactose"], "profiles": ["maintien_bien_etre"]},

    {"name": "Poulet tikka masala et riz basmati", "meal_type": "dinner", "calories": 560, "proteins_g": 40, "carbs_g": 58, "fats_g": 16, "allergens": ["lactose"], "profiles": ["prise_masse_debutant", "amelioration_cardio"]},
    {"name": "Truite grillée, légumes vapeur et quinoa", "meal_type": "dinner", "calories": 440, "proteins_g": 40, "carbs_g": 36, "fats_g": 14, "allergens": ["poisson"], "profiles": ["perte_poids_confirme", "amelioration_cardio"]},
    {"name": "Chili con carne haricots rouges et riz", "meal_type": "dinner", "calories": 520, "proteins_g": 36, "carbs_g": 60, "fats_g": 12, "allergens": [], "profiles": ["prise_masse_debutant", "amelioration_cardio"]},
    {"name": "Soupe thaï coco crevettes et citronnelle", "meal_type": "dinner", "calories": 340, "proteins_g": 24, "carbs_g": 22, "fats_g": 16, "allergens": ["crustaces"], "profiles": ["perte_poids_confirme", "maintien_bien_etre"]},
    {"name": "Salade César au poulet grillé", "meal_type": "lunch", "calories": 420, "proteins_g": 36, "carbs_g": 18, "fats_g": 22, "allergens": ["gluten", "lactose", "oeufs", "poisson"], "profiles": ["perte_poids_confirme", "maintien_bien_etre"]},
    {"name": "Coquilles Saint-Jacques poêlées et purée céleri", "meal_type": "dinner", "calories": 380, "proteins_g": 30, "carbs_g": 22, "fats_g": 16, "allergens": ["crustaces", "lactose"], "profiles": ["maintien_bien_etre", "perte_poids_confirme"]},
    {"name": "Crêpes sarrasin jambon-fromage", "meal_type": "lunch", "calories": 460, "proteins_g": 24, "carbs_g": 48, "fats_g": 18, "allergens": ["gluten", "lactose", "oeufs"], "profiles": ["maintien_bien_etre"]},
    {"name": "Tempeh grillé, riz noir et légumes asiatiques", "meal_type": "dinner", "calories": 480, "proteins_g": 28, "carbs_g": 58, "fats_g": 14, "allergens": ["soja", "gluten"], "profiles": ["prise_masse_debutant", "maintien_bien_etre"]},
    {"name": "Tartare de bœuf, frites de courgette et pain grillé", "meal_type": "dinner", "calories": 440, "proteins_g": 34, "carbs_g": 24, "fats_g": 22, "allergens": ["gluten", "oeufs"], "profiles": ["prise_masse_confirme", "perte_poids_confirme"]},
    {"name": "Bol acaï protéiné, granola et beurre d'amande", "meal_type": "breakfast", "calories": 480, "proteins_g": 18, "carbs_g": 58, "fats_g": 20, "allergens": ["gluten", "fruits_a_coque"], "profiles": ["amelioration_cardio", "prise_masse_debutant"]},
    {"name": "Toasts avocat-ricotta sur pain de levain", "meal_type": "breakfast", "calories": 390, "proteins_g": 14, "carbs_g": 38, "fats_g": 20, "allergens": ["gluten", "lactose"], "profiles": ["maintien_bien_etre", "amelioration_cardio"]},
    {"name": "Poêlée de quinoa, pois chiches et feta", "meal_type": "lunch", "calories": 440, "proteins_g": 20, "carbs_g": 54, "fats_g": 14, "allergens": ["lactose"], "profiles": ["maintien_bien_etre", "perte_poids_debutant"]},
    {"name": "Bœuf sauté aux poivrons et nouilles soba", "meal_type": "dinner", "calories": 550, "proteins_g": 38, "carbs_g": 58, "fats_g": 14, "allergens": ["gluten", "soja"], "profiles": ["prise_masse_confirme", "amelioration_cardio"]},
    {"name": "Salade de poulpe grillé, pommes de terre et câpres", "meal_type": "lunch", "calories": 360, "proteins_g": 28, "carbs_g": 32, "fats_g": 10, "allergens": ["crustaces"], "profiles": ["perte_poids_confirme", "maintien_bien_etre"]},
    {"name": "Gratin dauphinois et filet de veau rôti", "meal_type": "dinner", "calories": 620, "proteins_g": 38, "carbs_g": 44, "fats_g": 28, "allergens": ["lactose"], "profiles": ["prise_masse_confirme", "maintien_bien_etre"]},
    {"name": "Couscous royal légumes et merguez", "meal_type": "dinner", "calories": 640, "proteins_g": 32, "carbs_g": 72, "fats_g": 22, "allergens": ["gluten"], "profiles": ["amelioration_cardio", "prise_masse_debutant"]},
    {"name": "Soupe de pois cassés au jambon", "meal_type": "dinner", "calories": 320, "proteins_g": 24, "carbs_g": 38, "fats_g": 6, "allergens": [], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
    {"name": "Burritos haricots noirs, riz, guacamole", "meal_type": "lunch", "calories": 560, "proteins_g": 22, "carbs_g": 74, "fats_g": 18, "allergens": ["gluten"], "profiles": ["amelioration_cardio", "prise_masse_debutant"]},
    {"name": "Filet de bar en croûte d'amandes, légumes verts", "meal_type": "dinner", "calories": 420, "proteins_g": 36, "carbs_g": 12, "fats_g": 22, "allergens": ["poisson", "fruits_a_coque"], "profiles": ["perte_poids_confirme", "maintien_bien_etre"]},
    {"name": "Pancakes américains, sirop d'érable et myrtilles", "meal_type": "breakfast", "calories": 450, "proteins_g": 12, "carbs_g": 76, "fats_g": 12, "allergens": ["gluten", "lactose", "oeufs"], "profiles": ["amelioration_cardio"]},
    {"name": "Granola maison yaourt grec et kiwi", "meal_type": "breakfast", "calories": 340, "proteins_g": 14, "carbs_g": 48, "fats_g": 10, "allergens": ["gluten", "fruits_a_coque", "lactose"], "profiles": ["maintien_bien_etre", "amelioration_cardio"]},
    {"name": "Steak de thon mi-cuit, salade wakamé et gingembre", "meal_type": "lunch", "calories": 340, "proteins_g": 38, "carbs_g": 8, "fats_g": 14, "allergens": ["poisson", "soja", "gluten"], "profiles": ["perte_poids_confirme", "prise_masse_confirme"]},
    {"name": "Galette de sarrasin complète œuf-jambon-fromage", "meal_type": "lunch", "calories": 420, "proteins_g": 24, "carbs_g": 36, "fats_g": 18, "allergens": ["gluten", "oeufs", "lactose"], "profiles": ["maintien_bien_etre"]},
    {"name": "Ramen au bouillon de poulet, œuf mollet et légumes", "meal_type": "dinner", "calories": 480, "proteins_g": 28, "carbs_g": 60, "fats_g": 12, "allergens": ["gluten", "oeufs", "soja"], "profiles": ["amelioration_cardio", "prise_masse_debutant"]},
    {"name": "Dahl de lentilles corail, pain naan et riz", "meal_type": "dinner", "calories": 500, "proteins_g": 20, "carbs_g": 80, "fats_g": 10, "allergens": ["gluten"], "profiles": ["amelioration_cardio", "perte_poids_debutant"]},
    {"name": "Tartare de saumon avocat et crackers", "meal_type": "lunch", "calories": 380, "proteins_g": 26, "carbs_g": 22, "fats_g": 20, "allergens": ["poisson", "gluten"], "profiles": ["perte_poids_confirme", "maintien_bien_etre"]},
    {"name": "Bowl protéiné : edamame, riz, poulet, sauce sésame", "meal_type": "lunch", "calories": 560, "proteins_g": 42, "carbs_g": 58, "fats_g": 14, "allergens": ["soja", "fruits_a_coque", "gluten"], "profiles": ["prise_masse_confirme", "amelioration_cardio"]},
    {"name": "Quenelles de brochet sauce Nantua", "meal_type": "dinner", "calories": 420, "proteins_g": 26, "carbs_g": 28, "fats_g": 20, "allergens": ["poisson", "crustaces", "gluten", "lactose", "oeufs"], "profiles": ["maintien_bien_etre"]},
    {"name": "Salade de lentilles, betterave et chèvre chaud", "meal_type": "lunch", "calories": 380, "proteins_g": 18, "carbs_g": 42, "fats_g": 14, "allergens": ["lactose"], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
    {"name": "Poêlée de champignons, tofu et riz complet", "meal_type": "dinner", "calories": 380, "proteins_g": 20, "carbs_g": 52, "fats_g": 10, "allergens": ["soja", "gluten"], "profiles": ["perte_poids_debutant", "maintien_bien_etre"]},
]


def create_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id              SERIAL PRIMARY KEY,
            name            VARCHAR(255) NOT NULL,
            meal_type       VARCHAR(50)  NOT NULL,
            calories_kcal   FLOAT        NOT NULL,
            proteins_g      FLOAT        NOT NULL,
            carbs_g         FLOAT        NOT NULL,
            fats_g          FLOAT        NOT NULL,
            allergens       TEXT[]       NOT NULL DEFAULT '{}',
            profiles        TEXT[]       NOT NULL DEFAULT '{}',
            created_at      TIMESTAMP    DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_meals_type     ON meals(meal_type);
        CREATE INDEX IF NOT EXISTS idx_meals_profiles ON meals USING GIN(profiles);
        CREATE INDEX IF NOT EXISTS idx_meals_allergens ON meals USING GIN(allergens);
    """)


def seed(cur):
    cur.execute("DELETE FROM meals")
    for m in MEALS:
        cur.execute(
            """
            INSERT INTO meals (name, meal_type, calories_kcal, proteins_g, carbs_g, fats_g, allergens, profiles)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                m["name"], m["meal_type"],
                m["calories"], m["proteins_g"], m["carbs_g"], m["fats_g"],
                m["allergens"], m["profiles"],
            ),
        )
    return len(MEALS)


if __name__ == "__main__":
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute('SET search_path TO "Data"')
            create_table(cur)
            n = seed(cur)
        conn.commit()
    print(f"✓ Table meals créée — {n} repas insérés.")
