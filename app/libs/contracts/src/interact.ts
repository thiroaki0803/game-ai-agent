import fs from 'fs/promises';
import { Mina, NetworkId, PrivateKey, PublicKey, Field, fetchAccount } from 'o1js';
import { TruthLieContract } from './TruthLieContract.js';
import { generateStatements } from './generateStatements.js';

// Function to wait until the account exists
async function loopUntilAccountExists({
    account,
    eachTimeNotExist,
    isZkAppAccount,
}: {
    account: PublicKey;
    eachTimeNotExist: () => void;
    isZkAppAccount: boolean;
}) {
    while (true) {
        const response = await fetchAccount({ publicKey: account });
        let accountExists = response.account !== undefined;
        if (isZkAppAccount) {
            accountExists = response.account?.zkapp?.appState !== undefined;
        }
        if (!accountExists) {
            eachTimeNotExist();
            await new Promise((resolve) => setTimeout(resolve, 5000));
        } else {
            return response.account!;
        }
    }
}

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

const fee = Number(config.fee) * 1e9; // in nanomina
const feepayerAddress = feepayerKey.toPublicKey();

const zkAppAddress = zkAppKey.toPublicKey();
const zkApp = new TruthLieContract(zkAppAddress);

// Compile the contract to cache provers
console.log('Compiling the zkApp contract...');
await TruthLieContract.compile();

try {
    // Generate and set statements hash
    // Tentatively, we have assumed “2” as lie.
    const truth1 = "1";
    const truth2 = "3";
    const lie = "2";
    const statementsHash = generateStatements(truth1, truth2, lie);

    console.log('Generated statements hash:', statementsHash.toString());

    // Wait until the zkApp account exists
    await loopUntilAccountExists({
        account: zkAppAddress,
        eachTimeNotExist: () => console.log('zkApp account not found, retrying...'),
        isZkAppAccount: true
    });

    const memo = "Setting transaction";
    // Create and sign transaction
    const tx = await Mina.transaction(
        { sender: feepayerAddress, fee, memo: memo },
        async () => {
            console.log('Before setting hash:', (await zkApp.statementsHash.get()));
            await zkApp.setStatementsHash(Field(statementsHash));
            console.log('After setting hash:', (await zkApp.statementsHash.get()));
        }
    );

    try {
        console.log('Generating proof...');
        await tx.prove();
        console.log('Sending transaction...');
        const sentTx = await tx.sign([feepayerKey, zkAppKey]).send();
        console.log("Transaction status:", sentTx.status);

        if (sentTx.status === 'pending') {
            console.log(
                '\nSuccess! Update transaction sent.\n' +
                '\nYour smart contract state will be updated' +
                '\nas soon as the transaction is included in a block:' +
                `\n${getTxnUrl(config.url, sentTx.hash)}`
            );

            try {
                console.log('Waiting for transaction to succeed...');
                await sentTx.wait();
                console.log('Transaction successfully included in a block.');
            } catch (error) {
                console.error('Transaction was rejected or failed to be included in a block:', error);
            }
        } else {
            console.error('Transaction was not accepted for processing by the Mina daemon.');
        }
    } catch (err) {
        console.error('Error during transaction proof or sending:', err);
    }

} catch (err) {
    console.error('Error:', err);
}

// Function to get the transaction URL
function getTxnUrl(graphQlUrl: string, txnHash: string | undefined) {
    const hostName = new URL(graphQlUrl).hostname;
    const txnBroadcastServiceName = hostName
        .split('.')
        .filter((item) => item === 'minascan')?.[0];
    const networkName = graphQlUrl
        .split('/')
        .filter((item) => item === 'mainnet' || item === 'devnet')?.[0];
    if (txnBroadcastServiceName && networkName) {
        return `https://minascan.io/${networkName}/tx/${txnHash}?type=zk-tx`;
    }
    return `Transaction hash: ${txnHash}`;
}
