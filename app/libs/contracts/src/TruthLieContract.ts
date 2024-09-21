import { Field, SmartContract, state, State, method, Bool, Provable } from 'o1js';

/**
 * TruthLieContract
 * This contract manages a state variable `num` and `statementsHash`.
 * 
 * - `num` is initialized to Field(1) and can be incremented by 2 using `update`.
 * - `statementsHash` stores a hash value used for verification.
 * - `verifyStatement` method checks if a provided hash matches the stored hash.
 */
export class TruthLieContract extends SmartContract {
    @state(Field) statementsHash = State<Field>();

    @method.returns(Bool)
    async verifyStatement(userHash: Field): Promise<Bool> {
        // Fetch the stored hash from state
        const storedHash = this.statementsHash.get();

        // Ensure that the state is as expected
        this.statementsHash.requireEquals(storedHash);

        // Debug logs to understand the values
        Provable.log("User provided hash:", userHash);
        Provable.log("Stored hash:", storedHash);

        // Assert that the stored hash equals the user-provided hash
        return userHash.equals(storedHash);
    }
    @method async setStatementsHash(newHash: Field) {
        // Fetch the stored hash from state
        const storedHash = this.statementsHash.get();
        Provable.log("Stored hash:(setStatementsHash)", storedHash);

        // Ensure that the state is as expected
        this.statementsHash.requireEquals(storedHash);

        this.statementsHash.set(newHash);
        Provable.log("new hash:(setStatementsHash)", newHash);
    }
}
