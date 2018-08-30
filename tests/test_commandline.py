# coding: utf-8
# TODO
# test with the --output option
# test reading from standard input
from __future__ import print_function, division, absolute_import

import os
import shutil
import subprocess
import sys
import tempfile

import pytest

from cutadapt.__main__ import main
from cutadapt.compat import StringIO
from utils import run, assert_files_equal, datapath, cutpath, redirect_stderr, temporary_path

import pytest_timeout as _unused
del _unused


def test_example():
	run('-N -b ADAPTER', 'example.fa', 'example.fa')


def test_small():
	run('-b TTAGACATATCTCCGTCG', 'small.fastq', 'small.fastq')


def test_empty():
	"""empty input"""
	run('-a TTAGACATATCTCCGTCG', 'empty.fastq', 'empty.fastq')


def test_newlines():
	"""DOS/Windows newlines"""
	run('-e 0.12 -b TTAGACATATCTCCGTCG', 'dos.fastq', 'dos.fastq')


def test_lowercase():
	"""lowercase adapter"""
	run('-b ttagacatatctccgtcg', 'lowercase.fastq', 'small.fastq')


def test_rest():
	"""-r/--rest-file"""
	with temporary_path('rest.tmp') as rest_tmp:
		run(['-b', 'ADAPTER', '-N', '-r', rest_tmp], "rest.fa", "rest.fa")
		assert_files_equal(datapath('rest.txt'), rest_tmp)


def test_restfront():
	with temporary_path("rest.txt") as path:
		run(['-g', 'ADAPTER', '-N', '-r', path], "restfront.fa", "rest.fa")
		assert_files_equal(datapath('restfront.txt'), path)


def test_discard():
	"""--discard"""
	run("-b TTAGACATATCTCCGTCG --discard", "discard.fastq", "small.fastq")


def test_discard_untrimmed():
	"""--discard-untrimmed"""
	run('-b CAAGAT --discard-untrimmed', 'discard-untrimmed.fastq', 'small.fastq')


def test_plus():
	"""test if sequence name after the "+" is retained"""
	run("-e 0.12 -b TTAGACATATCTCCGTCG", "plus.fastq", "plus.fastq")


def test_extensiontxtgz():
	"""automatic recognition of "_sequence.txt.gz" extension"""
	run("-b TTAGACATATCTCCGTCG", "s_1_sequence.txt", "s_1_sequence.txt.gz")


def test_format():
	"""the -f/--format parameter"""
	run("-f fastq -b TTAGACATATCTCCGTCG", "small.fastq", "small.myownextension")


def test_minimum_length():
	"""-m/--minimum-length"""
	run("-c -m 5 -a 330201030313112312", "minlen.fa", "lengths.fa")


def test_too_short():
	"""--too-short-output"""
	run("-c -m 5 -a 330201030313112312 --too-short-output tooshort.tmp.fa", "minlen.fa", "lengths.fa")
	assert_files_equal(datapath('tooshort.fa'), "tooshort.tmp.fa")
	os.remove('tooshort.tmp.fa')


def test_too_short_no_primer():
	"""--too-short-output and --trim-primer"""
	run("-c -m 5 -a 330201030313112312 --trim-primer --too-short-output tooshort.tmp.fa", "minlen.noprimer.fa", "lengths.fa")
	assert_files_equal(datapath('tooshort.noprimer.fa'), "tooshort.tmp.fa")
	os.remove('tooshort.tmp.fa')


def test_maximum_length():
	"""-M/--maximum-length"""
	run("-c -M 5 -a 330201030313112312", "maxlen.fa", "lengths.fa")


def test_too_long():
	"""--too-long-output"""
	run("-c -M 5 --too-long-output toolong.tmp.fa -a 330201030313112312", "maxlen.fa", "lengths.fa")
	assert_files_equal(datapath('toolong.fa'), "toolong.tmp.fa")
	os.remove('toolong.tmp.fa')


def test_length_tag():
	"""454 data; -n and --length-tag"""
	run("-n 3 -e 0.1 --length-tag length= "
		"-b TGAGACACGCAACAGGGGAAAGGCAAGGCACACAGGGGATAGG "
		"-b TCCATCTCATCCCTGCGTGTCCCATCTGTTCCCTCCCTGTCTCA", '454.fa', '454.fa')


def test_overlap_a():
	"""-O/--overlap with -a (-c omitted on purpose)"""
	run("-O 10 -a 330201030313112312 -e 0.0 -N", "overlapa.fa", "overlapa.fa")


def test_overlap_b():
	"""-O/--overlap with -b"""
	run("-O 10 -b TTAGACATATCTCCGTCG -N", "overlapb.fa", "overlapb.fa")


def test_qualtrim():
	"""-q with low qualities"""
	run("-q 10 -a XXXXXX", "lowqual.fastq", "lowqual.fastq")


def test_qualbase():
	"""-q with low qualities, using ascii(quality+64) encoding"""
	run("-q 10 --quality-base 64 -a XXXXXX", "illumina64.fastq", "illumina64.fastq")


def test_quality_trim_only():
	"""only trim qualities, do not remove adapters"""
	run("-q 10 --quality-base 64", "illumina64.fastq", "illumina64.fastq")


def test_twoadapters():
	"""two adapters"""
	run("-a AATTTCAGGAATT -a GTTCTCTAGTTCT", "twoadapters.fasta", "twoadapters.fasta")


def test_polya():
	"""poly-A tails"""
	run("-m 24 -O 10 -a AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "polya.fasta", "polya.fasta")


def test_polya_brace_notation():
	"""poly-A tails"""
	run("-m 24 -O 10 -a A{35}", "polya.fasta", "polya.fasta")


# the same as --action=none
def test_no_trim():
	run("--no-trim --discard-untrimmed -a CCCTAGTTAAAC", 'no-trim.fastq', 'small.fastq')


def test_action_none():
	run("--action=none --discard-untrimmed -a CCCTAGTTAAAC", 'no-trim.fastq', 'small.fastq')


# the same as --action=mask
def test_mask_adapter():
	"""mask adapter with N (reads maintain the same length)"""
	run("-b CAAG -n 3 --mask-adapter", "anywhere_repeat.fastq", "anywhere_repeat.fastq")


def test_action_mask():
	"""mask adapter with N (reads maintain the same length)"""
	run("-b CAAG -n 3 --action=mask", "anywhere_repeat.fastq", "anywhere_repeat.fastq")


def test_gz_multiblock():
	"""compressed gz file with multiple blocks (created by concatenating two .gz files)"""
	run("-b TTAGACATATCTCCGTCG", "small.fastq", "multiblock.fastq.gz")


def test_suffix():
	"""-y/--suffix parameter, combined with _F3"""
	run("-c -e 0.12 -a 1=330201030313112312 -y _my_suffix_{name} --strip-f3", "suffix.fastq", "solid.csfasta", 'solid.qual')


def test_read_wildcard():
	"""test wildcards in reads"""
	run("--match-read-wildcards -b ACGTACGT", "wildcard.fa", "wildcard.fa")


def test_adapter_wildcard():
	"""wildcards in adapter"""
	for adapter_type, expected in (
			("-a", "wildcard_adapter.fa"),
			("-b", "wildcard_adapter_anywhere.fa")):
		with temporary_path("wildcardtmp.txt") as wildcardtmp:
			run("--wildcard-file {0} {1} ACGTNNNACGT".format(wildcardtmp, adapter_type),
				expected, "wildcard_adapter.fa")
			with open(wildcardtmp) as wct:
				lines = wct.readlines()
			lines = [ line.strip() for line in lines ]
			assert lines == ['AAA 1', 'GGG 2', 'CCC 3b', 'TTT 4b']


def test_wildcard_N():
	"""test 'N' wildcard matching with no allowed errors"""
	run("-e 0 -a GGGGGGG --match-read-wildcards", "wildcardN.fa", "wildcardN.fa")


def test_illumina_adapter_wildcard():
	run("-a VCCGAMCYUCKHRKDCUBBCNUWNSGHCGU", "illumina.fastq", "illumina.fastq.gz")


def test_adapter_front():
	"""test adapter in front"""
	run("--front ADAPTER -N", "examplefront.fa", "example.fa")


def test_literal_N():
	"""test matching literal 'N's"""
	run("-N -e 0.2 -a NNNNNNNNNNNNNN", "trimN3.fasta", "trimN3.fasta")


def test_literal_N2():
	run("-N -O 1 -g NNNNNNNNNNNNNN", "trimN5.fasta", "trimN5.fasta")


def test_literal_N_brace_notation():
	"""test matching literal 'N's"""
	run("-N -e 0.2 -a N{14}", "trimN3.fasta", "trimN3.fasta")


def test_literal_N2_brace_notation():
	run("-N -O 1 -g N{14}", "trimN5.fasta", "trimN5.fasta")


def test_anchored_front():
	run("-g ^FRONTADAPT -N", "anchored.fasta", "anchored.fasta")


def test_anchored_front_ellipsis_notation():
	run("-a FRONTADAPT... -N", "anchored.fasta", "anchored.fasta")


def test_anchored_back():
	run("-a BACKADAPTER$ -N", "anchored-back.fasta", "anchored-back.fasta")


def test_anchored_back_ellipsis_notation():
	run("-a ...BACKADAPTER$ -N", "anchored-back.fasta", "anchored-back.fasta")


def test_anchored_back_no_indels():
	run("-a BACKADAPTER$ -N --no-indels", "anchored-back.fasta", "anchored-back.fasta")


def test_no_indels():
	run('-a TTAGACATAT -g GAGATTGCCA --no-indels', 'no_indels.fasta', 'no_indels.fasta')


def test_ellipsis_notation():
	run('-a ...TTAGACATAT -g GAGATTGCCA --no-indels', 'no_indels.fasta', 'no_indels.fasta')


def test_issue_46():
	"""issue 46 - IndexError with --wildcard-file"""
	with temporary_path("wildcardtmp.txt") as wildcardtmp:
		run("--anywhere=AACGTN --wildcard-file={0}".format(wildcardtmp), "issue46.fasta", "issue46.fasta")


def test_strip_suffix():
	run("--strip-suffix _sequence -a XXXXXXX", "stripped.fasta", "simple.fasta")


def test_info_file():
	# The true adapter sequence in the illumina.fastq.gz data set is
	# GCCTAACTTCTTAGACTGCCTTAAGGACGT (fourth base is different)
	#
	with temporary_path("infotmp.txt") as infotmp:
		run(["--info-file", infotmp, '-a', 'adapt=GCCGAACTTCTTAGACTGCCTTAAGGACGT'],
			"illumina.fastq", "illumina.fastq.gz")
		assert_files_equal(cutpath('illumina.info.txt'), infotmp)


def test_info_file_times():
	with temporary_path("infotmp.txt") as infotmp:
		run(["--info-file", infotmp, '--times', '2', '-a', 'adapt=GCCGAACTTCTTA',
			'-a', 'adapt2=GACTGCCTTAAGGACGT'], "illumina5.fastq", "illumina5.fastq")
		assert_files_equal(cutpath('illumina5.info.txt'), infotmp)


def test_info_file_fasta():
	with temporary_path("infotmp.txt") as infotmp:
		# Just make sure that it runs
		run(['--info-file', infotmp, '-a', 'TTAGACATAT', '-g', 'GAGATTGCCA', '--no-indels'], 'no_indels.fasta', 'no_indels.fasta')


def test_named_adapter():
	run("-a MY_ADAPTER=GCCGAACTTCTTAGACTGCCTTAAGGACGT", "illumina.fastq", "illumina.fastq.gz")


def test_adapter_with_u():
	run("-a GCCGAACUUCUUAGACUGCCUUAAGGACGU", "illumina.fastq", "illumina.fastq.gz")


def test_bzip2():
	run('-b TTAGACATATCTCCGTCG', 'small.fastq', 'small.fastq.bz2')


if sys.version_info[:2] >= (3, 3):
	def test_bzip2_multiblock():
		run('-b TTAGACATATCTCCGTCG', 'small.fastq', 'multiblock.fastq.bz2')


try:
	import lzma

	def test_xz():
		run('-b TTAGACATATCTCCGTCG', 'small.fastq', 'small.fastq.xz')
except ImportError:
	pass


def test_qualfile_only():
	with pytest.raises(SystemExit):
		with redirect_stderr():
			main(['file.qual'])


def test_no_args():
	with pytest.raises(SystemExit):
		with redirect_stderr():
			main([])


def test_two_fastqs():
	with pytest.raises(SystemExit):
		with redirect_stderr():
			main([datapath('paired.1.fastq'), datapath('paired.2.fastq')])


def test_anchored_no_indels():
	"""anchored 5' adapter, mismatches only (no indels)"""
	run('-g ^TTAGACATAT --no-indels -e 0.1', 'anchored_no_indels.fasta', 'anchored_no_indels.fasta')


def test_anchored_no_indels_wildcard_read():
	"""anchored 5' adapter, mismatches only (no indels), but wildcards in the read count as matches"""
	run('-g ^TTAGACATAT --match-read-wildcards --no-indels -e 0.1', 'anchored_no_indels_wildcard.fasta', 'anchored_no_indels.fasta')


def test_anchored_no_indels_wildcard_adapt():
	"""anchored 5' adapter, mismatches only (no indels), but wildcards in the adapter count as matches"""
	run('-g ^TTAGACANAT --no-indels -e 0.1', 'anchored_no_indels.fasta', 'anchored_no_indels.fasta')


def test_non_iupac_characters():
	with pytest.raises(SystemExit):
		with redirect_stderr():
			main(['-a', 'ZACGT', datapath('small.fastq')])


def test_unconditional_cut_front():
	run('-u 5', 'unconditional-front.fastq', 'small.fastq')


def test_unconditional_cut_back():
	run('-u -5', 'unconditional-back.fastq', 'small.fastq')


def test_unconditional_cut_both():
	run('-u -5 -u 5', 'unconditional-both.fastq', 'small.fastq')


def test_untrimmed_output():
	with temporary_path('untrimmed.tmp.fastq') as tmp:
		run(['-a', 'TTAGACATATCTCCGTCG', '--untrimmed-output', tmp], 'small.trimmed.fastq', 'small.fastq')
		assert_files_equal(cutpath('small.untrimmed.fastq'), tmp)


def test_adapter_file():
	run('-a file:' + datapath('adapter.fasta'), 'illumina.fastq', 'illumina.fastq.gz')


def test_adapter_file_5p_anchored():
	run('-N -g file:' + datapath('prefix-adapter.fasta'), 'anchored.fasta', 'anchored.fasta')


def test_adapter_file_3p_anchored():
	run('-N -a file:' + datapath('suffix-adapter.fasta'), 'anchored-back.fasta', 'anchored-back.fasta')


def test_adapter_file_5p_anchored_no_indels():
	run('-N --no-indels -g file:' + datapath('prefix-adapter.fasta'), 'anchored.fasta', 'anchored.fasta')


def test_adapter_file_3p_anchored_no_indels():
	run('-N --no-indels -a file:' + datapath('suffix-adapter.fasta'), 'anchored-back.fasta', 'anchored-back.fasta')


def test_demultiplex():
	tempdir = tempfile.mkdtemp(prefix='cutadapt-tests.')
	multiout = os.path.join(tempdir, 'tmp-demulti.{name}.fasta')
	params = ['-a', 'first=AATTTCAGGAATT', '-a', 'second=GTTCTCTAGTTCT', '-o', multiout, datapath('twoadapters.fasta')]
	assert main(params) is None
	assert_files_equal(cutpath('twoadapters.first.fasta'), multiout.format(name='first'))
	assert_files_equal(cutpath('twoadapters.second.fasta'), multiout.format(name='second'))
	assert_files_equal(cutpath('twoadapters.unknown.fasta'), multiout.format(name='unknown'))
	shutil.rmtree(tempdir)


def test_max_n():
	run('--max-n 0', 'maxn0.fasta', 'maxn.fasta')
	run('--max-n 1', 'maxn1.fasta', 'maxn.fasta')
	run('--max-n 2', 'maxn2.fasta', 'maxn.fasta')
	run('--max-n 0.2', 'maxn0.2.fasta', 'maxn.fasta')
	run('--max-n 0.4', 'maxn0.4.fasta', 'maxn.fasta')


def test_quiet_is_quiet():
	captured_standard_output = StringIO()
	captured_standard_error = StringIO()
	old_stdout = sys.stdout
	old_stderr = sys.stderr
	try:
		sys.stdout = captured_standard_output
		sys.stderr = captured_standard_error
		main(['-o', '/dev/null', '--quiet', '-a', 'XXXX', datapath('illumina.fastq.gz')])
	finally:
		sys.stdout = old_stdout
		sys.stderr = old_stderr
	assert captured_standard_output.getvalue() == ''
	assert captured_standard_error.getvalue() == ''


def test_nextseq():
	run('--nextseq-trim 22', 'nextseq.fastq', 'nextseq.fastq')


def test_linked():
	run('-a AAAAAAAAAA...TTTTTTTTTT', 'linked.fasta', 'linked.fasta')


def test_linked_explicitly_anchored():
	run('-a ^AAAAAAAAAA...TTTTTTTTTT', 'linked.fasta', 'linked.fasta')


def test_linked_multiple():
	run('-a AAAAAAAAAA...TTTTTTTTTT -a AAAAAAAAAA...GCGCGCGCGC', 'linked.fasta', 'linked.fasta')


def test_linked_both_anchored():
	run('-a AAAAAAAAAA...TTTTT$', 'linked-anchored.fasta', 'linked.fasta')


def test_linked_5p_not_anchored():
	run('-g AAAAAAAAAA...TTTTTTTTTT', 'linked-not-anchored.fasta', 'linked.fasta')


def test_linked_discard_untrimmed():
	run('-a AAAAAAAAAA...TTTTTTTTTT --discard-untrimmed', 'linked-discard.fasta', 'linked.fasta')


def test_linked_discard_untrimmed_g():
	run('-g AAAAAAAAAA...TTTTTTTTTT --discard-untrimmed', 'linked-discard-g.fasta', 'linked.fasta')


def test_linked_anywhere():
	with pytest.raises(SystemExit):
		with redirect_stderr():
			main(['-b', 'AAA...TTT', datapath('linked.fasta')])


def test_anywhere_anchored_5p():
	with pytest.raises(SystemExit):
		with redirect_stderr():
			main(['-b', '^AAA', datapath('small.fastq')])


def test_anywhere_anchored_3p():
	with pytest.raises(SystemExit):
		with redirect_stderr():
			main(['-b', 'TTT$', datapath('small.fastq')])


def test_fasta():
	run('-a TTAGACATATCTCCGTCG', 'small.fasta', 'small.fastq')


def test_fasta_no_trim():
	run([], 'small-no-trim.fasta', 'small.fastq')


def test_issue_202():
	"""Ensure --length-tag= also modifies the second header line"""
	run('-a GGCTTC --length-tag=length=', 'SRR2040271_1.fastq', 'SRR2040271_1.fastq')


def test_length():
	run('--length 5', 'shortened.fastq', 'small.fastq')


def test_negative_length():
	run('--length -5', 'shortened-negative.fastq', 'small.fastq')


def test_run_cutadapt_process():
	subprocess.check_call(['cutadapt', '--version'])


@pytest.mark.timeout(0.5)
def test_issue_296(tmpdir):
	# Hang when using both --no-trim and --info-file together
	info_path = str(tmpdir.join('info.txt'))
	reads_path = str(tmpdir.join('reads.fasta'))
	out_path = str(tmpdir.join('out.fasta'))
	with open(reads_path, 'w') as f:
		f.write('>read\nCACAAA\n')
	main(['--info-file', info_path, '--no-trim', '-g', 'TTTCAC', '-o', out_path, reads_path])
	# Output should be unchanged because of --no-trim
	assert_files_equal(reads_path, out_path)


def test_xadapter():
	run('-g XTCCGAATAGA', 'xadapter.fasta', 'xadapterx.fasta')


def test_adapterx():
	run('-a TCCGAATAGAX', 'adapterx.fasta', 'xadapterx.fasta')


def test_discard_casava():
	run('--discard-casava', 'casava.fastq', 'casava.fastq')


@pytest.mark.xfail  # FIXME
def test_underscore():
	"""File name ending in _fastq.gz (issue #275)"""
	run('-b TTAGACATATCTCCGTCG', 'small.fastq', 'underscore_fastq.gz')
