"""Region identities used by the Part 4 published weather datasets."""

def weather_region_id(kind, number):
    number = int(number)
    if kind == 'EL' and 1 <= number <= 5:
        return f'NO{number}'
    if kind == 'NO' and number == 0:
        return 'NO0'
    if kind == 'VASS' and 1 <= number <= 3:
        return f'VASS{number}'
    raise ValueError(f'Unknown reservoir area: {kind} {number}.')

def validate_region_id(region_id):
    if region_id not in {*(f'NO{i}' for i in range(0, 6)), *(f'VASS{i}' for i in range(1, 4))}:
        raise ValueError('Choose a national, electricity or watercourse region.')
    return region_id
