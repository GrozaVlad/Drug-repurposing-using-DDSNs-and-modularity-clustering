CREATE TABLE public.all_drugs_info (
    name text,
    cas text,
    gene_target_ids_array text[],
    smiles_code text,
    inchi_code text,
    inchi_key text,
    molecular_formula text,
    atc_code text[],
    drugbank_version text
);

CREATE TABLE public.all_genes (
    name text,
    gene_id text,
    drugs_ids text[],
    drugbank_version text
);


CREATE TABLE public.drug_results (
    max_modularity text,
    candidates_number text,
    candidates_validated_number text,
    resolution text,
    drugbank_version text,
    candidates text[],
    candidates_validated text[]
);

CREATE TABLE public.drugs_resolution (
    name text,
    drugbank_version text,
    resolution text,
    modularity_class text
);