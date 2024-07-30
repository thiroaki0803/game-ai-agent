import json
import subprocess
import logging
from web3 import Web3
from zksync2.module.module_builder import ZkSyncBuilder

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZkSyncService:
    """
    zkSyncを操作するためのサービスクラス
    """

    def __init__(self, zksync_endpoint, contract_address, abi_path):
        """
        初期化メソッド

        :param zksync_endpoint: zkSyncのエンドポイントURL
        :param contract_address: zkSyncコントラクトのアドレス
        :param abi_path: zkSyncコントラクトのABIファイルのパス
        """
        self.zk_sync = ZkSyncBuilder.build(zksync_endpoint)
        self.contract_address = self._validate_address(contract_address)
        self.abi = self._load_abi(abi_path)

    def _validate_address(self, address):
        """アドレスを検証しチェックサム付きアドレスに変換"""
        try:
            return Web3.to_checksum_address(address)
        except ValueError as e:
            logger.error("Invalid Ethereum address: %s",e)

    def _load_abi(self, abi_path):
        """ABIファイルを読み込む"""
        try:
            with open(abi_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("ABI file not found: %s",  abi_path)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in ABI file: %s",  abi_path)

    @classmethod
    def generate_proof(cls, input_data, wasm_path, zkey_path):
        """
        zkSNARK証明を生成するクラスメソッド

        :param input_data: 入力データ
        :param wasm_path: 回路のwasmファイルパス
        :param zkey_path: zkeyファイルパス
        :return: 証明と公開信号のタプル
        """
        input_file = "input.json"
        witness_file = "witness.wtns"
        proof_file = "proof.json"
        public_file = "public.json"

        # input.jsonファイルに入力データを書き込み
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(input_data, f)

        try:
            # witness生成
            subprocess.run(
                ["snarkjs", "witness", "calculate", wasm_path, input_file, witness_file],
                check=True
            )

            # 証明生成
            subprocess.run(
                ["snarkjs", "groth16", "prove", zkey_path, witness_file, proof_file, public_file], 
                check=True
            )

            # 証明を読み込み
            with open(proof_file, "r", encoding="utf-8") as f:
                proof = json.load(f)

            # 公開信号を読み込み
            with open(public_file, "r", encoding="utf-8") as f:
                public_signals = json.load(f)

            return proof, public_signals
        except subprocess.CalledProcessError as e:
            logger.error("Error in snarkjs subprocess: %s", e)
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON: %s", e)

    def verify(self, correct, input_value):
        """
        データを検証するメソッド

        :param correct: 正しい値
        :param input_value: 検証する値
        :return: 検証結果 (True/False)
        :raises: ContractCallError 検証時にエラーが発生した場合
        """
        try:
            zksync_contract = self.zk_sync.eth.contract(
                address=self.contract_address, abi=self.abi
            )
            is_valid = zksync_contract.functions.verify(correct, input_value).call()
            return is_valid
        except Exception as e:
            logger.error("Error verifying data: %s", e)
