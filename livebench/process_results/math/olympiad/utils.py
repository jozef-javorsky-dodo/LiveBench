from livebench.process_results.util import last_boxed_only_string, remove_boxed

def match_expression_completions_to_ground_truth(completions, ground_truth):
    num_matches = 0
    for i in range(len(ground_truth)):
        if i not in completions:
            continue

        completion = completions[i].lower().strip().replace(' ' , '')
        comp = ground_truth[i].lower().strip().replace(' ' , '')

        if completion == comp:
            num_matches += 1

    return num_matches/len(ground_truth)

def remove_nonnumeric_chars_at_ends(s):
    start_index = 0
    while start_index < len(s) and not s[start_index].isdigit():
        start_index += 1
    end_index = start_index
    while end_index < len(s) and s[end_index].isdigit():
        end_index += 1

    return s[start_index:end_index], len(s) - (end_index - start_index)

def extract_expression_completions_from_generation(generation, debug):
    numbers = None
    if 'answer:' in generation.lower():
        lines = generation.lower().strip().split('\n')
        answer_str = None
        answer_line = None
        answer_index = None
        for i, line in enumerate(lines):
            if 'answer:' in line:
                answer_line = line
                answer_index = i
        answer_str = answer_line.split('answer:')[1].replace('answer:', '').replace('**', '').replace('.', '').strip()
        if answer_str == '' and answer_index < len(lines) - 1:
            answer_str = lines[answer_index+1].replace('answer:', '').replace('**', '').replace('.', '').strip()
        if numbers is None:
            numbers = []
        for n in answer_str.split(','):
            n = n.strip().split(' ')[-1].replace('$', '').replace('{', '').replace('}', '').replace('\\', '').replace('boxed', '').replace('<', '').replace('>', '')
            try:
                numbers.append(int(n))
            except:
                if debug:
                    print('ERROR', n)
                numbers.append('NO ANSWER')
        if len(numbers) == 0 or set(numbers) == {'NO ANSWER'}:
            numbers = None

    if numbers is None and '\\boxed' in generation:
        boxed = last_boxed_only_string(generation)
        if boxed is not None:
            no_box = remove_boxed(boxed)
            string = no_box
        else:
            string = generation
        string = string.replace('\\text{', '').replace('}', '').replace('\\', '')
        numbers = []
        for n in string.strip().split(','):
            try:
                numbers.append(int(n.strip()))
            except:
                numbers.append('NO ANSWER')
        if len(numbers) == 0 or set(numbers) == {'NO ANSWER'}:
            numbers = None

    if numbers is None:
        # try just the very last line of the generation
        last_line = generation.strip().lower().split('\n')[-1]
        numbers = []
        for n in last_line.strip().split(','):
            n, _ = remove_nonnumeric_chars_at_ends(n)
            if len(n.strip()) == 0:
                continue
            try:
                numbers.append(int(n.strip()))
            except:
                numbers.append('NO ANSWER')
        if len(numbers) == 0 or set(numbers) == {'NO ANSWER'}:
            numbers = None

    if numbers is None:
        # generation has Answer: comma separated list of numbers. I want to extract the last such comma separated list
        split_string = "answer:"
        numbers = [k.strip() for k in generation.lower().split(split_string)[-1].split(',')]

        # the last number may have some extra non-numeric characters at the end. Those need to be removed
        new_numbers = []
        for i, n in enumerate(numbers):
            n, num_removed = remove_nonnumeric_chars_at_ends(n)
            if n != '' and n != "₂":
                new_numbers.append(int(n))
            if (i > 0) and (num_removed > 0):
                break

        numbers = new_numbers
    
    return numbers

def proof_rearrangement_process_results(ground_truth: str, llm_answer: str, edit_distance=False, debug=False) -> int:
    ground_truth = [int(n) for n in ground_truth.split(',')]

    completions = extract_expression_completions_from_generation(llm_answer, debug)

    if edit_distance:
        from Levenshtein import distance
        match = distance(completions, ground_truth)
        frac_matches = 1-(match/max(len(completions), len(ground_truth)))
    else:
        match = [(completions[i] == ground_truth[i]) if i < len(ground_truth) else 0 for i in range(len(completions))]
        frac_matches = sum(match)/len(match) if len(match) > 0 else 0

    if debug and frac_matches < 1:
        print('INCORRECT', frac_matches)
        print('GROUND TRUTH', ground_truth)
        print('SOLUTION', completions)
        print('END OF OUTPUT', llm_answer[-1500:])

    return frac_matches

