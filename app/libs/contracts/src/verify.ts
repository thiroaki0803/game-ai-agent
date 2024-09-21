import fs from 'fs/promises';
import { TruthLieContract } from './TruthLieContract.js';
import { boolToJavaScript, generateStatements } from './generateStatements.js';
import { fetchAccount, Mina, NetworkId, PrivateKey } from 'o1js';

// Check command line args
const deployAlias = process.argv[2];

if (!deployAlias) {
    throw new Error(`Missing <deployAlias> argument.`);
}

const DEFAULT_NETWORK_ID = 'testnet';

// Parse config and private key from file
type Config = {
    deployAliases: Record<
        string,
        {
            networkId?: string;
            url: string;
            keyPath: string;
            fee: string;
            feepayerKeyPath: string;
            feepayerAlias: string;
        }
    >;
};

let configJson: Config = JSON.parse(await fs.readFile('libs/contracts/config.json', 'utf8'));
let config = configJson.deployAliases[deployAlias];
let feepayerKeysBase58: { privateKey: string; publicKey: string } = JSON.parse(
    await fs.readFile(config.feepayerKeyPath, 'utf8')
);

let zkAppKeysBase58: { privateKey: string; publicKey: string } = JSON.parse(
    await fs.readFile(config.keyPath, 'utf8')
);

let feepayerKey = PrivateKey.fromBase58(feepayerKeysBase58.privateKey);
let zkAppKey = PrivateKey.fromBase58(zkAppKeysBase58.privateKey);

// Set up Mina instance and contract
const Network = Mina.Network({
    networkId: (config.networkId ?? DEFAULT_NETWORK_ID) as NetworkId,
    mina: config.url,
});

Mina.setActiveInstance(Network);

const zkAppAddress = zkAppKey.toPublicKey();

// Instantiate the worker
const worker = new TruthLieContract(zkAppAddress);

// Example usage
async function run() {
    try {
        await fetchAccount({ publicKey: zkAppAddress });
        const userStatement = process.argv[3];
        const truth1 = "1";
        const truth2 = "3";

        const providedHash = generateStatements(truth1, truth2, userStatement);

        const result = await worker.verifyStatement(providedHash);
        let resultInBoolean = await boolToJavaScript(result);
        console.log(resultInBoolean);
    } catch (error) {
        console.error('Error:', error);
        process.exit(1);
    }
}

run();
