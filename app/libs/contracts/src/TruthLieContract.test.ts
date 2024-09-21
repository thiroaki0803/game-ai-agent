import { AccountUpdate, Bool, Field, Mina, PrivateKey, PublicKey } from 'o1js';
import { TruthLieContract } from './TruthLieContract.js';
import { boolToJavaScript, generateStatements } from './generateStatements.js';

let proofsEnabled = false;

describe('TruthLieContract', () => {
  let deployerAccount: Mina.TestPublicKey,
    deployerKey: PrivateKey,
    senderAccount: Mina.TestPublicKey,
    senderKey: PrivateKey,
    zkAppAddress: PublicKey,
    zkAppPrivateKey: PrivateKey,
    zkApp: TruthLieContract;

  beforeAll(async () => {
    if (proofsEnabled) await TruthLieContract.compile();
  });

  beforeEach(async () => {
    const Local = await Mina.LocalBlockchain({ proofsEnabled });
    Mina.setActiveInstance(Local);
    [deployerAccount, senderAccount] = Local.testAccounts;
    deployerKey = deployerAccount.key;
    senderKey = senderAccount.key;

    zkAppPrivateKey = PrivateKey.random();
    zkAppAddress = zkAppPrivateKey.toPublicKey();
    zkApp = new TruthLieContract(zkAppAddress);
  });

  async function localDeploy() {
    const txn = await Mina.transaction(deployerAccount, async () => {
      AccountUpdate.fundNewAccount(deployerAccount);
      zkApp.deploy();
      zkApp.init(); // Initialize the contract state
    });
    await txn.prove();
    await txn.sign([deployerKey, zkAppPrivateKey]).send();
  }

  it('correctly verifies the statement hash on the `TruthLieContract` smart contract', async () => {
    try {
      await localDeploy();

      // Generate a test hash for verification
      const testHash = Field(123456789);

      // Set the hash on the contract
      const setTxn = await Mina.transaction(senderAccount, async () => {
        await zkApp.setStatementsHash(testHash);
      });
      await setTxn.prove();
      await setTxn.sign([senderKey]).send();

      // Verify the statement hashy
      const truth1 = "I am an AI";
      const truth2 = "I can help with code";
      const lie = "I don't need any input";
      const statementsHash = generateStatements(truth1, truth2, lie);

      console.log('Setting statement hash...');
      const verifyTxn = await Mina.transaction(senderAccount, async () => {
        await zkApp.setStatementsHash(Field(statementsHash)); // Ensure hash is set before verification
      });
      await verifyTxn.prove();
      await verifyTxn.sign([senderKey]).send();

      console.log('Verifying statement...');
      const isSuccess = await zkApp.verifyStatement(Field(statementsHash));
      const isSuccessJavaScript = await boolToJavaScript(isSuccess);
      console.log('Verification result:', isSuccessJavaScript);

      // Assert that the verification is successful
      expect(isSuccessJavaScript).toBe(true);
    } catch (err) {
      console.error('Error during test execution:', err);
      throw err;
    }
  });
});
