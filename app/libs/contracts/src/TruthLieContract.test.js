"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
const o1js_1 = require("o1js");
const TruthLieContract_js_1 = require("./TruthLieContract.js");
const generateStatements_js_1 = require("./generateStatements.js");
let proofsEnabled = false;
describe('TruthLieContract', () => {
    let deployerAccount, deployerKey, senderAccount, senderKey, zkAppAddress, zkAppPrivateKey, zkApp;
    beforeAll(() => __awaiter(void 0, void 0, void 0, function* () {
        if (proofsEnabled)
            yield TruthLieContract_js_1.TruthLieContract.compile();
    }));
    beforeEach(() => __awaiter(void 0, void 0, void 0, function* () {
        const Local = yield o1js_1.Mina.LocalBlockchain({ proofsEnabled });
        o1js_1.Mina.setActiveInstance(Local);
        [deployerAccount, senderAccount] = Local.testAccounts;
        deployerKey = deployerAccount.key;
        senderKey = senderAccount.key;
        zkAppPrivateKey = o1js_1.PrivateKey.random();
        zkAppAddress = zkAppPrivateKey.toPublicKey();
        zkApp = new TruthLieContract_js_1.TruthLieContract(zkAppAddress);
    }));
    function localDeploy() {
        return __awaiter(this, void 0, void 0, function* () {
            const txn = yield o1js_1.Mina.transaction(deployerAccount, () => __awaiter(this, void 0, void 0, function* () {
                o1js_1.AccountUpdate.fundNewAccount(deployerAccount);
                zkApp.deploy();
                zkApp.init(); // Initialize the contract state
            }));
            yield txn.prove();
            yield txn.sign([deployerKey, zkAppPrivateKey]).send();
        });
    }
    it('correctly verifies the statement hash on the `TruthLieContract` smart contract', () => __awaiter(void 0, void 0, void 0, function* () {
        try {
            yield localDeploy();
            // Generate a test hash for verification
            const testHash = (0, o1js_1.Field)(123456789);
            // Set the hash on the contract
            const setTxn = yield o1js_1.Mina.transaction(senderAccount, () => __awaiter(void 0, void 0, void 0, function* () {
                yield zkApp.setStatementsHash(testHash);
            }));
            yield setTxn.prove();
            yield setTxn.sign([senderKey]).send();
            // Verify the statement hashy
            const truth1 = "I am an AI";
            const truth2 = "I can help with code";
            const lie = "I don't need any input";
            const statementsHash = (0, generateStatements_js_1.generateStatements)(truth1, truth2, lie);
            console.log('Setting statement hash...');
            const verifyTxn = yield o1js_1.Mina.transaction(senderAccount, () => __awaiter(void 0, void 0, void 0, function* () {
                yield zkApp.setStatementsHash((0, o1js_1.Field)(statementsHash)); // Ensure hash is set before verification
            }));
            yield verifyTxn.prove();
            yield verifyTxn.sign([senderKey]).send();
            console.log('Verifying statement...');
            const isSuccess = yield zkApp.verifyStatement((0, o1js_1.Field)(statementsHash));
            const isSuccessJavaScript = yield (0, generateStatements_js_1.boolToJavaScript)(isSuccess);
            console.log('Verification result:', isSuccessJavaScript);
            // Assert that the verification is successful
            expect(isSuccessJavaScript).toBe(true);
        }
        catch (err) {
            console.error('Error during test execution:', err);
            throw err;
        }
    }));
});
