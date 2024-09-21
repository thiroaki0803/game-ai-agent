import { Field, SmartContract, State, Bool } from 'o1js';
/**
 * TruthLieContract
 * This contract manages a state variable `num` and `statementsHash`.
 *
 * - `num` is initialized to Field(1) and can be incremented by 2 using `update`.
 * - `statementsHash` stores a hash value used for verification.
 * - `verifyStatement` method checks if a provided hash matches the stored hash.
 */
export declare class TruthLieContract extends SmartContract {
    statementsHash: State<import("o1js/dist/node/lib/provable/field").Field>;
    verifyStatement(userHash: Field): Promise<Bool>;
    setStatementsHash(newHash: Field): Promise<void>;
}
