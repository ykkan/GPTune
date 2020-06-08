#!/bin/bash -l
#SBATCH -q premium
#SBATCH -N 17
#SBATCH -t 10:00:00
#SBATCH -J GPTune_scalapack
#SBATCH --mail-user=liuyangzhuan@lbl.gov
#SBATCH -C haswell
#SBATCH -A m2957


module load python/3.7-anaconda-2019.10
module unload cray-mpich/7.7.6

module swap PrgEnv-intel PrgEnv-gnu
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/compilers_and_libraries_2019.3.199/linux/mkl/lib/intel64

module load openmpi/4.0.1

export PYTHONPATH=$PYTHONPATH:$PWD/autotune/
export PYTHONPATH=$PYTHONPATH:$PWD/scikit-optimize/
export PYTHONPATH=$PYTHONPATH:$PWD/mpi4py/
export PYTHONPATH=$PYTHONPATH:$PWD/GPTune/
export PYTHONPATH=$PYTHONPATH:$PWD/examples/scalapack-driver/spt/
export PYTHONWARNINGS=ignore

CCC=mpicc
CCCPP=mpicxx
FTN=mpif90

cd examples


# mpirun --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata.py -mmax 5000 -nmax 5000 -nodes 128 -cores 4 -ntask 20 -nrun 20 -machine cori1 -jobid 0 | tee a.out_scalapck_ML_m5000_n5000_nodes128_core4_ntask20_nrun20
# -N: number of ranks per node
# mpirun -N 32 --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata.py -mmax 20000 -nmax 20000 -nodes 256 -cores 2 -ntask 20 -nrun 20 -machine cori1 -jobid 0 | tee a.out_scalapck_ML_m20000_n20000_nodes256_core2_ntask50_nrun20
# mpirun -N 32 -map-by node:PE=1 --bind-to core --rank-by socket:span --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata.py -mmax 20000 -nmax 20000 -nodes 256 -cores 2 -ntask 1 -nrun 40 -machine cori1 -jobid 0 | tee a.out_scalapck_ML_m20000_n20000_nodes256_core2_ntask50_nrun20

for nrun in 10
do


mmax=40000
nmax=40000
ntask=1
nrun1=`expr $nrun / 2`
nodes=256
cores=2

rm -rf *.pkl
tuner='GPTune'
mpirun --oversubscribe -N 32 --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata_initial.py -mmax ${mmax} -nmax ${nmax} -nodes ${nodes} -cores ${cores} -ntask ${ntask} -nrun ${nrun1} -machine cori1 -jobid 0 -optimization ${tuner}| tee a.out_scalapck_ML_m${mmax}_n${nmax}_nodes${nodes}_core${cores}_ntask${ntask}_nrun${nrun}_${tuner}_oversubscribe_initial

mpirun --oversubscribe -N 32 --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata_modelfit.py -mmax ${mmax} -nmax ${nmax} -nodes ${nodes} -cores ${cores} -ntask ${ntask} -nrun ${nrun} -machine cori1 -jobid 0 -optimization ${tuner}| tee a.out_scalapck_ML_m${mmax}_n${nmax}_nodes${nodes}_core${cores}_ntask${ntask}_nrun${nrun}_${tuner}_oversubscribe_modelfit


mpirun --oversubscribe -N 32 --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata_nomodel.py -mmax ${mmax} -nmax ${nmax} -nodes ${nodes} -cores ${cores} -ntask ${ntask} -nrun ${nrun} -machine cori1 -jobid 0 -optimization ${tuner}| tee a.out_scalapck_ML_m${mmax}_n${nmax}_nodes${nodes}_core${cores}_ntask${ntask}_nrun${nrun}_${tuner}_oversubscribe_nomodel


# mpirun --oversubscribe -N 32 --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata_modelsimple.py -mmax ${mmax} -nmax ${nmax} -nodes ${nodes} -cores ${cores} -ntask ${ntask} -nrun ${nrun} -machine cori1 -jobid 0 -optimization ${tuner}| tee a.out_scalapck_ML_m${mmax}_n${nmax}_nodes${nodes}_core${cores}_ntask${ntask}_nrun${nrun}_${tuner}_oversubscribe_modelsimple

done
