CREATE OR REPLACE VIEW pokemon_with_moves AS
SELECT 
    pokemon.name as pokemon_name, 
    `move`.`name` as move_name,
    damage,
    `type`.`name` as type_name
FROM pokemon_move
LEFT JOIN `move`
    ON `move`.id = pokemon_move.move_id
LEFT JOIN pokemon
    ON pokemon.id=pokemon_move.pokemon_id
LEFT JOIN `type`
    ON `type`.id =`move`.type_id;