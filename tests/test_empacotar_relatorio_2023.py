"""Regressões de versão e integridade do ZIP, sem calcular estatísticas."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from empacotar_relatorio_2023 import package, references, verify_archive


class PackageVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'tmp')
        self.root=Path(self.temp.name)
        for name in ['main.tex','modelos/main.tex','validacao_relatorio_2023.json','tabelas/indicadores.tex']:
            dest=self.root/'DOCUMENT'/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/'DOCUMENT'/name,dest)
        for name in references((ROOT/'DOCUMENT/main.tex').read_text(encoding='utf-8')):
            if name.startswith('../resultados/'):
                dest=self.root/'DOCUMENT'/name
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/'DOCUMENT'/name,dest)

    def tearDown(self):
        self.temp.cleanup()

    def run_package(self):
        with redirect_stdout(io.StringIO()):
            return package(self.root)

    def test_current_source_dependencies_and_aliases_are_identical(self):
        result=self.run_package()
        self.assertTrue(result['task13_confirmada'])
        self.assertTrue(all(v['iguais'] for v in result['sha256_internos_vs_locais'].values()))
        output=self.root/result['arquivo']
        for alias in result['copias_identicas']:
            self.assertEqual(output.read_bytes(),(self.root/alias).read_bytes())
        with zipfile.ZipFile(output) as z:
            self.assertEqual(z.read('main.tex').decode('utf-8').replace('graficos/','../resultados/graficos/'),
                             (self.root/'DOCUMENT/main.tex').read_text(encoding='utf-8'))
            self.assertIn('FGPercentualBrancosUnifor',z.read('main.tex').decode('utf-8'))
            self.assertIn(r'\newcommand{\FGPercentualBrancosUnifor}{32,0}',z.read('tabelas/indicadores.tex').decode('utf-8-sig'))

    def test_stale_validation_cannot_be_packaged(self):
        for name in ['main.tex','modelos/main.tex']:
            path=self.root/'DOCUMENT'/name
            path.write_bytes(path.read_bytes()+b'\n% modified\n')
        with self.assertRaisesRegex(ValueError,'versão validada'):
            self.run_package()

    def test_changed_member_is_detected_by_sha256(self):
        result=self.run_package()
        archive=self.root/result['arquivo']
        with zipfile.ZipFile(archive) as z:
            contents={n:z.read(n) for n in z.namelist()}
        contents['tabelas/indicadores.tex']+=b'\n% changed\n'
        tampered=self.root/'tampered.zip'
        with zipfile.ZipFile(tampered,'w') as z:
            for name,data in contents.items():
                z.writestr(name,data)
        with self.assertRaisesRegex(ValueError,'SHA-256 divergente'):
            verify_archive(tampered,self.root/'DOCUMENT/pacote_latex',contents)

    def test_same_content_reproduces_same_zip_and_version(self):
        first=self.run_package()
        before=(self.root/first['arquivo']).read_bytes()
        second=self.run_package()
        self.assertEqual(first['versao'],second['versao'])
        self.assertEqual(before,(self.root/second['arquivo']).read_bytes())


if __name__=='__main__':
    unittest.main()
