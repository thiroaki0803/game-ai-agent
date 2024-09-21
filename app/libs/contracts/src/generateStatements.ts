import { Bool, Field, Poseidon } from 'o1js';

function stringToField(str: string): Field {
    const utf8Bytes = new TextEncoder().encode(str);
    let num = BigInt(0);
    for (const byte of utf8Bytes) {
        num = (num << BigInt(8)) | BigInt(byte);
    }
    return Field(num);
}

/**
 * //Two Truths and A Lie Logic
 * 
 * Generates a Poseidon hash from three input statements: two truths and one lie.
 * 
 * This function converts the provided strings into `Field` objects, computes the Poseidon hash of these fields, 
 * and returns the resulting hash as a `Field` object.
 * 
 * @param {string} truth1 - The first statement that is a truth. This is a string that represents a true fact.
 * @param {string} truth2 - The second statement that is a truth. This is another string that represents a second true fact.
 * @param {string} lie - The statement that is a lie. This string represents a false fact that is used in contrast to the truths.
 * 
 * @returns {Field} - A `Field` object containing the Poseidon hash of the three input statements.
 * 
 * @example
 * // Define the statements
 * const truth1 = "I am an AI";
 * const truth2 = "I can help with code";
 * const lie = "I don't need any input";
 * 
 * // Generate the hash for the truth and lie statements
 * const statementsHash = generateStatements(truth1, truth2, lie);
 * 
 * // Generate a hash for a provided statement (which should be a lie)
 * const provided = "I don't need any input";
 * const providedHash = generateStatements(truth1, truth2, provided);
 * 
 * // Log the hashes to compare
 * console.log("Statements Hash:", statementsHash.toString());
 * console.log("Provided Hash:", providedHash.toString());
 */
export function generateStatements(truth1: string, truth2: string, lie: string): Field {
    const truth1Field = stringToField(truth1);
    const truth2Field = stringToField(truth2);
    const lieField = stringToField(lie);

    // Compute the hash using Poseidon
    return Poseidon.hash([truth1Field, truth2Field, lieField]);
}
/**
 * Converts a Mina `Bool` value to a JavaScript boolean.
 * 
 * This function takes a Mina `Bool` type value and converts it to a standard JavaScript boolean. 
 * It compares the `Bool` value to `Bool(true)` to determine if it represents true, and then 
 * returns the corresponding JavaScript boolean value (`true` or `false`).
 * 
 * @param {Bool} boolValue - The Mina `Bool` value to be converted. It represents a boolean value within the Mina blockchain environment.
 * 
 * @returns {Promise<boolean>} - A `Promise` that resolves to a JavaScript boolean value. 
 *                               It will be `true` if `boolValue` is equivalent to `Bool(true)`, otherwise it will be `false`.
 * 
 * @example
 * // Example usage in an async function
 * const minaBool = Bool(true); // Mina Bool value
 * const jsBool = await boolToJavaScript(minaBool); // Converts to JavaScript boolean
 * console.log(jsBool); // Outputs: true
 * 
 * // Another example where minaBool is false
 * const minaBoolFalse = Bool(false);
 * const jsBoolFalse = await boolToJavaScript(minaBoolFalse);
 * console.log(jsBoolFalse); // Outputs: false
 */
// Function to check if a `Bool` value represents true
export async function boolToJavaScript(boolValue: Bool): Promise<boolean> {
    // Use the `.equals()` method to compare to `Bool(true)`
    return boolValue.equals(Bool(true)).toBoolean();
}
