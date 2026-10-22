"""Repete preparação e aprofundamento com blocos diferentes e compara bytes."""
import json
import subprocess
import sys

from preparar_2023 import ROOT, require, sha256


def verify_repro(root=ROOT):
    audit = json.loads((root/'resultados/tabelas/validacao_aprofundamento_2023.json').read_text(encoding='utf-8'))
    require(all(r['lidos'] > 0 for r in audit['leitura'].values()), 'Leitura original não registrada')
    names = sorted(set(audit['sha256_saidas']) | set(audit['sha256_entradas']))
    before = {n: sha256(root/n) for n in names}
    (root/'tmp').mkdir(exist_ok=True)
    with (root/'tmp/reprodutibilidade_execucao.log').open('w', encoding='utf-8') as log:
        for script in ['preparar_2023.py', 'aprofundar_2023.py']:
            subprocess.run([sys.executable, str(root/'src'/script), '--chunksize', '17000'],
                           cwd=root, check=True, stdout=log, stderr=log)
    after = {n: sha256(root/n) for n in names}
    changed = [n for n in names if before[n] != after[n]]
    result = {'status': 'aprovado' if not changed else 'falha',
              'chunksize_reexecucao': 17000, 'arquivos_comparados': len(names),
              'diferencas': changed, 'sha256_antes': before, 'sha256_depois': after}
    (root/'resultados/tabelas/validacao_reprodutibilidade_2023.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    require(not changed, f'Resultados não reprodutíveis: {changed}')
    print(f'Reprodutibilidade aprovada: {len(names)} arquivos idênticos, incluindo CSV, PNG e PDF.')
    return result


if __name__ == '__main__':
    verify_repro()
